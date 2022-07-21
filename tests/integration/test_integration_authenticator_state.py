import asyncio
import os

from aiounittest import AsyncTestCase

from conjur_api import Client
from conjur_api.errors.errors import HttpStatusError
from conjur_api.models import SslVerificationMode, ConjurConnectionInfo, CredentialsData
from conjur_api.providers import SimpleCredentialsProvider


class ConjurUser:
    def __init__(self, user_id: str, api_key: str):
        self.id = user_id
        self.api_key = api_key


class TestEnableDisableAuthenticators(AsyncTestCase):
    conjur_url = "https://conjur-https"
    account = "dev"
    isFirstTime = True

    @classmethod
    def setUpClass(cls):
        asyncio.run(cls._add_test_data())

    async def test_authenticator_enable_success(self):
        c = await self._create_client(self.valid_user.id, self.valid_user.api_key)
        response = await c.set_authenticator_state('authn-iam/test', True)

        self.assertEqual(response, '')

    async def test_authenticator_disable_success(self):
        c = await self._create_client(self.valid_user.id, self.valid_user.api_key)
        response = await c.set_authenticator_state('authn-iam/test', False)

        self.assertEqual(response, '')

    async def test_authenticator_enable_no_permissions(self):
        c = await self._create_client(self.invalid_user.id, self.invalid_user.api_key)

        with self.assertRaises(HttpStatusError) as context:
            response = await c.set_authenticator_state('authn-iam/test', True)
        self.assertEqual(context.exception.status, 403)

    async def test_authenticator_disable_no_permissions(self):
        c = await self._create_client(self.invalid_user.id, self.invalid_user.api_key)
        with self.assertRaises(HttpStatusError) as context:
            response = await c.set_authenticator_state('authn-iam/test', False)
        self.assertEqual(context.exception.status, 403)

    async def test_enable_non_existing_authenticator(self):
        c = await self._create_client(self.valid_user.id, self.valid_user.api_key)

        with self.assertRaises(HttpStatusError) as context:
            response = await c.set_authenticator_state('authn-iam/non-existing', True)
        self.assertEqual(context.exception.status, 401)

    async def test_disable_non_existing_authenticator(self):
        c = await self._create_client(self.valid_user.id, self.valid_user.api_key)
        with self.assertRaises(HttpStatusError) as context:
            response = await c.set_authenticator_state('authn-iam/non-existing', False)
        self.assertEqual(context.exception.status, 401)

    @classmethod
    async def _add_test_data(cls):
        c = await cls._create_client("admin", os.environ['CONJUR_AUTHN_API_KEY'])
        response = await c.load_policy_file('root', 'tests/integration/policies/root.yml')
        valid_user: ConjurUser = ConjurUser(user_id='test-authenticator-valid-user',
                                            api_key=response['created_roles']['dev:user:test-authenticator-valid-user']
                                            ['api_key'])
        invalid_user: ConjurUser = ConjurUser(user_id='test-authenticator-invalid-user',
                                              api_key=response['created_roles']['dev:user:test-authenticator-invalid-user']
                                              ['api_key'])
        response = await c.load_policy_file('conjur', 'tests/integration/policies/authn-iam-test.yml')

        cls.valid_user = valid_user
        cls.invalid_user = invalid_user

    @classmethod
    async def _create_client(cls, username: str, password: str) -> Client:
        conjur_data = ConjurConnectionInfo(
            conjur_url=cls.conjur_url,
            account=cls.account
        )
        credentials_provider = SimpleCredentialsProvider()
        credentials = CredentialsData(username=username, password=password, machine=cls.conjur_url)
        credentials_provider.save(credentials)
        return Client(conjur_data, credentials_provider=credentials_provider,
                      ssl_verification_mode=SslVerificationMode.INSECURE)
