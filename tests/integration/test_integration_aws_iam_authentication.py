import asyncio
import contextlib
import os
import tempfile

import pytest
from aiounittest import AsyncTestCase

from conjur_api import Client
from conjur_api.models import ConjurConnectionInfo, SslVerificationMode
from conjur_api.providers.aws_iam_authentication_strategy import AWSIAMAuthenticationStrategy
from tests.integration.integ_utils import create_admin_client


_AUTHN_IAM_POLICY_TEMPLATE = """\
- !policy
  id: prod
  body:
  - !webservice
  - !group clients
  - !permit
    role: !group clients
    privilege: [ read, authenticate ]
    resource: !webservice
  - !grant
    role: !group clients
    member: !host /data/test/myspace/{account_id}/{role_name}
"""

_IAM_ROLES_POLICY_TEMPLATE = """\
- !policy
  id: myspace
  body:
  - &variables
    - !variable database/username
    - !variable database/password
  - !group secrets-users
  - !permit
    role: !group secrets-users
    privilege: [ read, execute ]
    resource: *variables
  - !layer
  - !host
    id: "{account_id}/{role_name}"
  - !grant
    role: !layer
    member: !host "{account_id}/{role_name}"
  - !grant
    member: !layer
    role: !group secrets-users
"""


def _skip_unless_aws():
    if os.getenv("RUN_AWS_TESTS") != "true":
        pytest.skip("RUN_AWS_TESTS is not set to 'true'")


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
class TestAWSIAMAuthentication(AsyncTestCase):

    @classmethod
    def setUpClass(cls):
        _skip_unless_aws()
        asyncio.run(cls._setup())

    @classmethod
    async def _setup(cls):
        aws_account_id = os.environ["AWS_ACCOUNT_ID"]
        aws_role_name = os.environ["AWS_ROLE_NAME"]
        cls.conjur_identity = f"host/data/test/myspace/{aws_account_id}/{aws_role_name}"
        cls.conjur_url = "https://conjur-https"
        cls.account = "conjur"

        c = await create_admin_client()

        # Load the host policy first so the grant in the authn-iam policy can reference it
        roles_policy = _IAM_ROLES_POLICY_TEMPLATE.format(
            account_id=aws_account_id,
            role_name=aws_role_name,
        )
        with _temp_policy(roles_policy) as roles_policy_file:
            await c.load_policy_file("data/test", roles_policy_file)

        authn_iam_policy = _AUTHN_IAM_POLICY_TEMPLATE.format(
            account_id=aws_account_id,
            role_name=aws_role_name,
        )
        with _temp_policy(authn_iam_policy) as authn_iam_policy_file:
            await c.load_policy_file("conjur/authn-iam", authn_iam_policy_file)

        await c.set("data/test/myspace/database/username", "secret")
        await c.set("data/test/myspace/database/password", "P@ssw0rd!")  # nosec

        await c.set_authenticator_state("authn-iam/prod", True)

    async def test_aws_iam_instance_profile(self):
        _skip_unless_aws()
        connection_info = ConjurConnectionInfo(
            conjur_url=self.conjur_url,
            account=self.account,
            service_id="prod",
        )
        strategy = AWSIAMAuthenticationStrategy(
            identity=self.conjur_identity,
            service_id="prod",
        )
        c = Client(
            connection_info,
            authn_strategy=strategy,
            ssl_verification_mode=SslVerificationMode.INSECURE,
            debug=True,
        )
        response = await c.whoami()
        self.assertEqual(response["username"], self.conjur_identity)
