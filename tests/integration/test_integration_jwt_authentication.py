import asyncio

import pytest
import requests
from aiounittest import AsyncTestCase
from requests.auth import HTTPBasicAuth

from conjur_api.errors.errors import HttpStatusError
from tests.integration.integ_utils import (AuthenticationStrategyType,
                                           create_admin_client, create_client)


@pytest.mark.integration
class TestJWTAuthentication(AsyncTestCase):

    @classmethod
    def setUpClass(cls):
        asyncio.run(cls._add_test_data())

    async def test_jwt_authentication_success(self):
        c = await create_client("", self.valid_jwt, AuthenticationStrategyType.JWT,
                                service_id='test-service')

        response = await c.whoami()
        self.assertTrue(response['username'] == 'host/workload@example.com')

    async def test_jwt_authentication_failure_invalid_token(self):
        c = await create_client("", self.invalid_jwt, AuthenticationStrategyType.JWT,
                                service_id='test-service')

        with self.assertRaises(HttpStatusError) as context:
            response = await c.whoami()
        self.assertEqual(context.exception.status, 401)

    @classmethod
    async def _add_test_data(cls):
        c = await create_admin_client()
        await c.set('conjur/authn-jwt/test-service/jwks-uri', 'http://jwt-server:8080/.well-known/jwks.json')
        await c.set('conjur/authn-jwt/test-service/token-app-property', 'email')
        await c.set('conjur/authn-jwt/test-service/audience', 'conjur')
        await c.set('conjur/authn-jwt/test-service/issuer', 'jwt-server')

        url = 'http://jwt-server:8080/token'

        # file deepcode ignore SSLVerificationBypass/test: This is a test file and we are using a local server
        x = requests.get(url, verify=False)

        cls.valid_jwt = x.json()['token']
        cls.invalid_jwt = 'invalid_token'
