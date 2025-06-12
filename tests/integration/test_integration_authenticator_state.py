import asyncio

import pytest
from aiounittest import AsyncTestCase

from conjur_api.errors.errors import HttpStatusError
from conjur_api.models import Resource
from tests.integration.integ_utils import (ConjurUser, create_admin_client,
                                           create_client)


@pytest.mark.integration
class TestEnableDisableAuthenticators(AsyncTestCase):

    @classmethod
    def setUpClass(cls):
        asyncio.run(cls._add_test_data())

    async def test_authenticator_enable_success(self):
        c = await create_client(self.valid_user.id, self.valid_user.secret)
        response = await c.set_authenticator_state('authn-iam/test', True)

        self.assertEqual(response, '')

    async def test_authenticator_disable_success(self):
        c = await create_client(self.valid_user.id, self.valid_user.secret)
        response = await c.set_authenticator_state('authn-iam/test', False)

        self.assertEqual(response, '')

    async def test_authenticator_enable_twice_success(self):
        c = await create_client(self.valid_user.id, self.valid_user.secret)

        response = await c.set_authenticator_state('authn-iam/test', True)
        self.assertEqual(response, '')
        response = await c.set_authenticator_state('authn-iam/test', True)
        self.assertEqual(response, '')

    async def test_authenticator_disable_twice_success(self):
        c = await create_client(self.valid_user.id, self.valid_user.secret)

        response = await c.set_authenticator_state('authn-iam/test', False)
        self.assertEqual(response, '')
        response = await c.set_authenticator_state('authn-iam/test', False)
        self.assertEqual(response, '')

    async def test_authenticator_enable_no_permissions(self):
        c = await create_client(self.invalid_user.id, self.invalid_user.secret)

        with self.assertRaises(HttpStatusError) as context:
            response = await c.set_authenticator_state('authn-iam/test', True)
        self.assertEqual(context.exception.status, 403)

    async def test_authenticator_disable_no_permissions(self):
        c = await create_client(self.invalid_user.id, self.invalid_user.secret)
        with self.assertRaises(HttpStatusError) as context:
            response = await c.set_authenticator_state('authn-iam/test', False)
        self.assertEqual(context.exception.status, 403)

    async def test_enable_non_existing_authenticator(self):
        c = await create_client(self.valid_user.id, self.valid_user.secret)

        with self.assertRaises(HttpStatusError) as context:
            response = await c.set_authenticator_state('authn-iam/non-existing', True)
        self.assertEqual(context.exception.status, 401)

    async def test_disable_non_existing_authenticator(self):
        c = await create_client(self.valid_user.id, self.valid_user.secret)
        with self.assertRaises(HttpStatusError) as context:
            response = await c.set_authenticator_state('authn-iam/non-existing', False)
        self.assertEqual(context.exception.status, 401)

    async def test_authenticator_enable_without_service_id_success(self):
        c = await create_client(self.valid_user.id, self.valid_user.secret)
        response = await c.set_authenticator_state('authn-gcp', True)

        self.assertEqual(response, '')

    async def test_authenticator_disable_without_service_id_success(self):
        c = await create_client(self.valid_user.id, self.valid_user.secret)
        response = await c.set_authenticator_state('authn-gcp', False)

        self.assertEqual(response, '')

    async def test_authenticator_enable_failure_while_auth_without_service_id(self):
        c = await create_client(self.invalid_user.id, self.invalid_user.secret)
        with self.assertRaises(HttpStatusError) as context:
            response = await c.set_authenticator_state('authn-gcp', True)
        self.assertEqual(context.exception.status, 403)

    async def test_authenticator_disable_failure_while_auth_without_service_id(self):
        c = await create_client(self.invalid_user.id, self.invalid_user.secret)
        with self.assertRaises(HttpStatusError) as context:
            response = await c.set_authenticator_state('authn-gcp', False)
        self.assertEqual(context.exception.status, 403)

    @classmethod
    async def _add_test_data(cls):
        c = await create_admin_client()
        response = await c.rotate_other_api_key(Resource('user', 'test-valid-user'))
        valid_user: ConjurUser = ConjurUser(user_id='test-valid-user', secret=response)
        response = await c.rotate_other_api_key(Resource('user', 'test-invalid-user'))
        invalid_user: ConjurUser = ConjurUser(user_id='test-invalid-user', secret=response)
        cls.valid_user = valid_user
        cls.invalid_user = invalid_user
