import asyncio
import os

import requests
from aiounittest import AsyncTestCase
from requests.auth import HTTPBasicAuth

from conjur_api.errors.errors import HttpStatusError
from tests.integration.integ_utils import create_client, ConjurUser, AuthenticationStrategyType


class TestOidcAuthentication(AsyncTestCase):

    @classmethod
    def setUpClass(cls):
        asyncio.run(cls._add_test_data())

    async def test_oidc_authentication_success(self):
        c = await create_client(self.valid_user.id, self.valid_user.secret, AuthenticationStrategyType.OIDC,
                                service_id='test-service')

        response = await c.whoami()
        self.assertTrue(response['username'] == 'john.williams')

    async def test_oidc_authentication_failure_invalid_token(self):
        c = await create_client(self.valid_user.id, 'invalid_token', AuthenticationStrategyType.OIDC,
                                service_id='test-service')

        with self.assertRaises(HttpStatusError) as context:
            response = await c.whoami()
        self.assertEqual(context.exception.status, 401)

    @classmethod
    async def _add_test_data(cls):
        c = await create_client("admin", os.environ['CONJUR_AUTHN_API_KEY'])
        await c.set('conjur/authn-oidc/test-service/provider-uri', 'https://oidc-server')
        await c.set('conjur/authn-oidc/test-service/id-token-user-property', 'sub')

        url = 'https://oidc-server/connect/token'
        headers = {'content-type': 'application/x-www-form-urlencoded'}
        body = {'grant_type': 'password', 'username': 'john.williams', 'password': 'pwd', 'scope': 'openid'}

        x = requests.post(url, data=body, headers=headers, verify=False,
                          auth=HTTPBasicAuth('client-credentials-mock-client', 'client-credentials-mock-client-secret'))

        cls.valid_user: ConjurUser = ConjurUser(user_id='john.williams', secret=x.json()['access_token'])
