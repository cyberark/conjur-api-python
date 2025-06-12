import asyncio
import json

import pytest
import requests
from aiounittest import AsyncTestCase
from requests.auth import HTTPBasicAuth

from conjur_api.errors.errors import HttpStatusError
from tests.integration.integ_utils import (AuthenticationStrategyType,
                                           create_admin_client, create_client)


@pytest.mark.integration
@pytest.mark.cloud
class TestJWTAuthentication(AsyncTestCase):

    @classmethod
    def setUpClass(cls):
        asyncio.run(cls._add_test_data())

    async def test_jwt_authentication_success(self):
        c = await create_client("", self.valid_jwt, AuthenticationStrategyType.JWT,
                                service_id='test-service')

        response = await c.whoami()
        self.assertEqual(response['username'], 'host/data/workload@example.com')

    async def test_jwt_authentication_failure_invalid_token(self):
        c = await create_client("", self.invalid_jwt, AuthenticationStrategyType.JWT,
                                service_id='test-service')

        with self.assertRaises(HttpStatusError) as context:
            response = await c.whoami()
        self.assertEqual(context.exception.status, 401)

    @classmethod
    async def _add_test_data(cls):
        c = await create_admin_client()
        # Set up the JWT authenticator in Conjur
        await c.load_policy_file("data", "tests/integration/policies/common.yml")
        await c.load_policy_file("conjur/authn-jwt", "tests/integration/policies/authn-jwt.yml")
        await c.set_authenticator_state('authn-jwt/test-service', True)
        
        # Fetch the public keys from the JWKS URI
        # Using public-keys instead of jwks_uri allows us to use the local
        # mock JWT server even when testing against Conjur Cloud, since
        # Conjur Cloud does not need to be able to reach the mock JWT server.
        jwks_uri = 'http://jwt-server:8080/.well-known/jwks.json'
        jwks = requests.get(jwks_uri, verify=False)
        pubkeys = {
            "type": "jwks",
            "value": jwks.json()
        }
    
        await c.set('conjur/authn-jwt/test-service/public-keys', json.dumps(pubkeys))
        await c.set('conjur/authn-jwt/test-service/token-app-property', 'email')
        await c.set('conjur/authn-jwt/test-service/audience', 'conjur')
        await c.set('conjur/authn-jwt/test-service/issuer', 'jwt-server')
        await c.set('conjur/authn-jwt/test-service/identity-path', 'data')

        url = 'http://jwt-server:8080/token'

        # file deepcode ignore SSLVerificationBypass/test: This is a test file and we are using a local server
        x = requests.get(url, verify=False)

        cls.valid_jwt = x.json()['token']
        cls.invalid_jwt = 'invalid_token'
