import asyncio
import base64
import contextlib
import json
import os
import tempfile

import pytest
from aiounittest import AsyncTestCase
from aiohttp import ClientSession, ClientTimeout

from conjur_api import Client
from conjur_api.models import ConjurConnectionInfo, SslVerificationMode
from conjur_api.providers.azure_authentication_strategy import AzureAuthenticationStrategy
from tests.integration.integ_utils import create_admin_client


_AUTHN_AZURE_POLICY = """\
- !policy
  id: prod
  body:
  - !webservice
  - !variable
    id: provider-uri
  - !group apps
  - !permit
    role: !group apps
    privilege: [ read, authenticate ]
    resource: !webservice
  - !grant
    role: !group apps
    member: !host /data/test/azure-apps/azureVM
"""

_AZURE_APPS_POLICY_SYSTEM = """\
- !policy
  id: azure-apps
  body:
  - &variables
    - !variable database/username
    - !variable database/password
  - !group secrets-users
  - !permit
    role: !group secrets-users
    privilege: [ read, execute ]
    resource: *variables
  - !group
  - !host
    id: azureVM
    annotations:
      authn-azure/subscription-id: {subscription_id}
      authn-azure/resource-group: {resource_group}
  - !grant
    role: !group
    member: !host azureVM
  - !grant
    member: !group
    role: !group secrets-users
"""

_AZURE_APPS_POLICY_USER_ASSIGNED = """\
- !policy
  id: azure-apps
  body:
  - &variables
    - !variable database/username
    - !variable database/password
  - !group secrets-users
  - !permit
    role: !group secrets-users
    privilege: [ read, execute ]
    resource: *variables
  - !group
  - !host
    id: azureVM
    annotations:
      authn-azure/subscription-id: {subscription_id}
      authn-azure/resource-group: {resource_group}
      authn-azure/user-assigned-identity: {user_identity}
  - !grant
    role: !group
    member: !host azureVM
  - !grant
    member: !group
    role: !group secrets-users
"""

_AZURE_IDENTITY = "host/data/test/azure-apps/azureVM"


def _skip_unless_azure():
    if os.getenv("RUN_AZURE_TESTS") != "true":
        pytest.skip("RUN_AZURE_TESTS is not set to 'true'")


async def _resolve_provider_uri(client_id=None) -> str:
    url = (
        "http://169.254.169.254/metadata/identity/oauth2/token"
        "?api-version=2018-02-01&resource=https%3A%2F%2Fmanagement.azure.com%2F"
    )
    if client_id:
        url += f"&client_id={client_id}"

    async with ClientSession(trust_env=False, timeout=ClientTimeout(total=20)) as session:
        async with session.get(url, headers={"Metadata": "true"}) as resp:
            text = await resp.text()
            if not resp.ok:
                raise RuntimeError(f"IMDS returned {resp.status}: {text}")

    body = json.loads(text)
    token = body.get("access_token", "")
    if not token:
        raise RuntimeError(f"IMDS response missing access_token: {text}")
    # Decode the JWT payload (second segment, base64url-encoded)
    payload_b64 = token.split(".")[1]
    # Add padding so base64 doesn't complain
    payload_b64 += "=" * (4 - len(payload_b64) % 4)
    payload = json.loads(base64.urlsafe_b64decode(payload_b64))
    iss = payload["iss"]
    # Ensure trailing slash (Conjur requires it)
    return iss if iss.endswith("/") else iss + "/"


@contextlib.contextmanager
def _temp_policy(content: str):
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False)
    try:
        f.write(content)
        f.flush()
        f.close()
        yield f.name
    finally:
        os.unlink(f.name)


@pytest.mark.integration
class TestAzureAuthentication(AsyncTestCase):

    @classmethod
    def setUpClass(cls):
        _skip_unless_azure()
        asyncio.run(cls._setup())

    @classmethod
    async def _setup(cls):
        subscription_id = os.environ["AZURE_SUBSCRIPTION_ID"]
        resource_group = os.environ["AZURE_RESOURCE_GROUP"]
        cls.user_identity = os.getenv("USER_ASSIGNED_IDENTITY", "")
        cls.user_identity_client_id = os.getenv("USER_ASSIGNED_IDENTITY_CLIENT_ID", "")

        c = await create_admin_client()

        # Load data/test/azure-apps first so the host exists before the grant in authn-azure references it
        system_policy = _AZURE_APPS_POLICY_SYSTEM.format(
            subscription_id=subscription_id,
            resource_group=resource_group,
        )
        with _temp_policy(system_policy) as system_policy_file:
            await c.load_policy_file("data/test", system_policy_file)

        # Now load conjur/authn-azure which grants the host access to the webservice
        with _temp_policy(_AUTHN_AZURE_POLICY) as authn_azure_file:
            await c.load_policy_file("conjur/authn-azure", authn_azure_file)

        # Resolve provider-uri from IMDS (system-assigned identity)
        provider_uri = await _resolve_provider_uri()
        await c.set("conjur/authn-azure/prod/provider-uri", provider_uri)
        await c.set("data/test/azure-apps/database/username", "secret")
        await c.set("data/test/azure-apps/database/password", "P@ssw0rd!")  # nosec

        await c.set_authenticator_state("authn-azure/prod", True)

        cls.conjur_url = "https://conjur-https"
        cls.account = "conjur"

    def _make_azure_client(self, client_id=None) -> Client:
        connection_info = ConjurConnectionInfo(
            conjur_url=self.conjur_url,
            account=self.account,
            service_id="prod",
        )
        strategy = AzureAuthenticationStrategy(
            identity=_AZURE_IDENTITY,
            client_id=client_id,
        )
        return Client(
            connection_info,
            authn_strategy=strategy,
            ssl_verification_mode=SslVerificationMode.INSECURE,
            debug=True,
        )

    async def test_azure_system_assigned_identity(self):
        _skip_unless_azure()
        c = self._make_azure_client()
        response = await c.whoami()
        self.assertEqual(response["username"], _AZURE_IDENTITY)

    async def test_azure_user_assigned_identity(self):
        _skip_unless_azure()
        if not self.user_identity_client_id:
            pytest.skip("USER_ASSIGNED_IDENTITY_CLIENT_ID not set")

        # Re-load policy with user-assigned annotation and update provider-uri
        subscription_id = os.environ["AZURE_SUBSCRIPTION_ID"]
        resource_group = os.environ["AZURE_RESOURCE_GROUP"]
        user_policy = _AZURE_APPS_POLICY_USER_ASSIGNED.format(
            subscription_id=subscription_id,
            resource_group=resource_group,
            user_identity=self.user_identity,
        )
        c_admin = await create_admin_client()
        with _temp_policy(user_policy) as user_policy_file:
            await c_admin.load_policy_file("data/test", user_policy_file)

        provider_uri = await _resolve_provider_uri(client_id=self.user_identity_client_id)
        await c_admin.set("conjur/authn-azure/prod/provider-uri", provider_uri)

        c = self._make_azure_client(client_id=self.user_identity_client_id)
        response = await c.whoami()
        self.assertEqual(response["username"], _AZURE_IDENTITY)
