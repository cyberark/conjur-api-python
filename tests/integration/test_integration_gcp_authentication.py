import asyncio
import contextlib
import os
import tempfile

import pytest
from aiounittest import AsyncTestCase

from conjur_api import Client
from conjur_api.models import ConjurConnectionInfo, SslVerificationMode
from conjur_api.providers.gcp_authentication_strategy import GCPAuthenticationStrategy
from tests.integration.integ_utils import create_admin_client


_AUTHN_JWT_GCP_POLICY = """\
- !policy
  id: gcp
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
    member: !host /data/test/gcp-apps/test-app
"""

_GCP_APPS_POLICY_TEMPLATE = """\
- !policy
  id: gcp-apps
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
    id: test-app
    annotations:
      authn-jwt/gcp/google/compute_engine/project_id: "{project_id}"
  - !grant
    role: !group
    member: !host test-app
  - !grant
    member: !group
    role: !group secrets-users
"""

_GCP_IDENTITY = "host/data/test/gcp-apps/test-app"


def _skip_unless_gcp():
    if os.getenv("RUN_GCP_TESTS") != "true":
        pytest.skip("RUN_GCP_TESTS is not set to 'true'")


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
class TestGCPAuthentication(AsyncTestCase):

    @classmethod
    def setUpClass(cls):
        _skip_unless_gcp()
        asyncio.run(cls._setup())

    @classmethod
    async def _setup(cls):
        gcp_project_id = os.environ["GCP_PROJECT_ID"]
        cls.gcp_id_token = os.environ["GCP_ID_TOKEN"]
        cls.conjur_url = "https://conjur-https"
        cls.account = "conjur"

        c = await create_admin_client()

        # Load host policy first so the grant in the authn-jwt/gcp policy can reference it
        gcp_apps_policy = _GCP_APPS_POLICY_TEMPLATE.format(project_id=gcp_project_id)
        with _temp_policy(gcp_apps_policy) as gcp_apps_file:
            await c.load_policy_file("data/test", gcp_apps_file)

        with _temp_policy(_AUTHN_JWT_GCP_POLICY) as authn_jwt_gcp_file:
            await c.load_policy_file("conjur/authn-jwt", authn_jwt_gcp_file)

        await c.set("conjur/authn-jwt/gcp/provider-uri", "https://accounts.google.com")
        await c.set("data/test/gcp-apps/database/username", "secret")
        await c.set("data/test/gcp-apps/database/password", "P@ssw0rd!")  # nosec

        await c.set_authenticator_state("authn-jwt/gcp", True)

    async def test_gcp_explicit_token(self):
        _skip_unless_gcp()
        connection_info = ConjurConnectionInfo(
            conjur_url=self.conjur_url,
            account=self.account,
            service_id="gcp",
        )
        strategy = GCPAuthenticationStrategy(
            identity=_GCP_IDENTITY,
            jwt=self.gcp_id_token,
        )
        c = Client(
            connection_info,
            authn_strategy=strategy,
            ssl_verification_mode=SslVerificationMode.INSECURE,
            debug=True,
        )
        response = await c.whoami()
        self.assertEqual(response["username"], _GCP_IDENTITY)
