import asyncio
import os

from aiounittest import AsyncTestCase

from conjur_api.errors.errors import HttpStatusError
from conjur_api.models import Resource
from tests.integration.integ_utils import create_client, ConjurUser


class TestEnableDisableAuthenticators(AsyncTestCase):

    @classmethod
    def setUpClass(cls):
        asyncio.run(cls._add_test_data())

    async def setUp(self):
        self.valid_user = await self._create_user("test-valid-user")
        self.invalid_user = await self._create_user("test-invalid-user")

    async def _create_user(self, user_id):
        c = await create_client("admin", os.environ['CONJUR_AUTHN_API_KEY'])
        response = await c.rotate_other_api_key(Resource('user', user_id))
        return ConjurUser(user_id=user_id, secret=response)

    async def _test_authenticator_state(self, auth_state):
        c = await create_client(self.valid_user.id, self.valid_user.secret)
        response = await c.set_authenticator_state(
                'authn-iam/test',
                auth_state
            )
        self.assertEqual(response, '')

    async def test_authenticator_enable_success(self):
        await self._test_authenticator_state(True)

    async def test_authenticator_disable_success(self):
        await self._test_authenticator_state(False)

    async def test_authenticator_enable_twice_success(self):
        await self._test_authenticator_state(True)
        await self._test_authenticator_state(True)

    async def test_authenticator_disable_twice_success(self):
        await self._test_authenticator_state(False)
        await self._test_authenticator_state(False)

    async def test_authenticator_enable_no_permissions(self):
        await self._test_authenticator_state(True, self.invalid_user)

    async def test_authenticator_disable_no_permissions(self):
        await self._test_authenticator_state(False, self.invalid_user)

    async def test_enable_disable_non_existing_authenticator(self):
        with self.assertRaises(HttpStatusError) as context:
            await self._test_authenticator_state(True, user=None)
        self.assertEqual(context.exception.status, 401)

    async def test_authenticator_enable_failure_while_auth_without_service_id(
                self
            ):
        await self._test_authenticator_state(
                True,
                self.invalid_user,
                'authn-gcp',
                403
            )

    async def test_authenticator_disable_failure_while_auth_without_service_id(
                self
            ):
        await self._test_authenticator_state(
                False,
                self.invalid_user,
                'authn-gcp',
                403
            )

    async def _test_authenticator_state(
                self,
                auth_state,
                user=None,
                auth_id='authn-iam/test',
                expected_status=200
            ):
        user_id = self.valid_user.id if user is None else user.id
        secret = self.valid_user.secret if user is None else user.secret

        c = await create_client(user_id, secret)
        response = await c.set_authenticator_state(auth_id, auth_state)
        self.assertEqual(response.status, expected_status)

    @classmethod
    async def _add_test_data(cls):
        c = await create_client("admin", os.environ['CONJUR_AUTHN_API_KEY'])
        response = await c.rotate_other_api_key(
                Resource('user', 'test-valid-user')
            )
        cls.valid_user = ConjurUser(user_id='test-valid-user', secret=response)
        response = await c.rotate_other_api_key(
                Resource('user', 'test-invalid-user')
            )
        cls.invalid_user = ConjurUser(
                user_id='test-invalid-user',
                secret=response
            )
