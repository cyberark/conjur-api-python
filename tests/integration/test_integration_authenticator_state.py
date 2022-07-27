import asyncio
import os

from aiounittest import AsyncTestCase

from conjur_api.errors.errors import HttpStatusError
from tests.integration.integ_utils import create_client


class ConjurUser:
    def __init__(self, user_id: str, api_key: str):
        self.id = user_id
        self.api_key = api_key


class TestEnableDisableAuthenticators(AsyncTestCase):

    @classmethod
    def setUpClass(cls):
        asyncio.run(cls._add_test_data())

    async def test_authenticator_enable_success(self):
        c = await create_client(self.valid_user.id, self.valid_user.api_key)
        response = await c.set_authenticator_state('authn-iam/test', True)

        self.assertEqual(response, '')

    async def test_authenticator_disable_success(self):
        c = await create_client(self.valid_user.id, self.valid_user.api_key)
        response = await c.set_authenticator_state('authn-iam/test', False)

        self.assertEqual(response, '')

    async def test_authenticator_enable_twice_success(self):
        c = await create_client(self.valid_user.id, self.valid_user.api_key)

        response = await c.set_authenticator_state('authn-iam/test', True)
        self.assertEqual(response, '')
        response = await c.set_authenticator_state('authn-iam/test', True)
        self.assertEqual(response, '')

    async def test_authenticator_disable_twice_success(self):
        c = await create_client(self.valid_user.id, self.valid_user.api_key)

        response = await c.set_authenticator_state('authn-iam/test', False)
        self.assertEqual(response, '')
        response = await c.set_authenticator_state('authn-iam/test', False)
        self.assertEqual(response, '')

    async def test_authenticator_enable_no_permissions(self):
        c = await create_client(self.invalid_user.id, self.invalid_user.api_key)

        with self.assertRaises(HttpStatusError) as context:
            response = await c.set_authenticator_state('authn-iam/test', True)
        self.assertEqual(context.exception.status, 403)

    async def test_authenticator_disable_no_permissions(self):
        c = await create_client(self.invalid_user.id, self.invalid_user.api_key)
        with self.assertRaises(HttpStatusError) as context:
            response = await c.set_authenticator_state('authn-iam/test', False)
        self.assertEqual(context.exception.status, 403)

    async def test_enable_non_existing_authenticator(self):
        c = await create_client(self.valid_user.id, self.valid_user.api_key)

        with self.assertRaises(HttpStatusError) as context:
            response = await c.set_authenticator_state('authn-iam/non-existing', True)
        self.assertEqual(context.exception.status, 401)

    async def test_disable_non_existing_authenticator(self):
        c = await create_client(self.valid_user.id, self.valid_user.api_key)
        with self.assertRaises(HttpStatusError) as context:
            response = await c.set_authenticator_state('authn-iam/non-existing', False)
        self.assertEqual(context.exception.status, 401)

    async def test_authenticator_enable_without_service_id_success(self):
        c = await create_client(self.valid_user.id, self.valid_user.api_key)
        response = await c.set_authenticator_state('authn-gcp', True)

        self.assertEqual(response, '')

    async def test_authenticator_disable_without_service_id_success(self):
        c = await create_client(self.valid_user.id, self.valid_user.api_key)
        response = await c.set_authenticator_state('authn-gcp', False)

        self.assertEqual(response, '')

    async def test_authenticator_enable_failure_while_auth_without_service_id(self):
        c = await create_client(self.invalid_user.id, self.invalid_user.api_key)
        with self.assertRaises(HttpStatusError) as context:
            response = await c.set_authenticator_state('authn-gcp', True)
        self.assertEqual(context.exception.status, 403)

    async def test_authenticator_disable_failure_while_auth_without_service_id(self):
        c = await create_client(self.invalid_user.id, self.invalid_user.api_key)
        with self.assertRaises(HttpStatusError) as context:
            response = await c.set_authenticator_state('authn-gcp', False)
        self.assertEqual(context.exception.status, 403)

    @classmethod
    async def _add_test_data(cls):
        c = await create_client("admin", os.environ['CONJUR_AUTHN_API_KEY'])
        response = await c.load_policy_file('root', 'tests/integration/policies/root.yml')
        valid_user: ConjurUser = ConjurUser(user_id='test-authenticator-valid-user',
                                            api_key=response['created_roles']['dev:user:test-authenticator-valid-user']
                                            ['api_key'])
        invalid_user: ConjurUser = ConjurUser(user_id='test-authenticator-invalid-user',
                                              api_key=response['created_roles']['dev:user:test-authenticator-invalid-user']
                                              ['api_key'])
        response = await c.load_policy_file('conjur', 'tests/integration/policies/authn-iam-test.yml')
        response = await c.load_policy_file('conjur', 'tests/integration/policies/authn-gcp.yml')

        cls.valid_user = valid_user
        cls.invalid_user = invalid_user
