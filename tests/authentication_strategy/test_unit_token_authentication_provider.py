from datetime import datetime

from aiounittest import AsyncTestCase

from conjur_api.models.general.conjur_connection_info import \
    ConjurConnectionInfo
from conjur_api.models.general.credentials_data import CredentialsData
from conjur_api.providers import TokenAuthenticationStrategy
from conjur_api.providers.simple_credentials_provider import \
    SimpleCredentialsProvider


class TokenAuthenticationStrategyTest(AsyncTestCase):
    
    async def test_doesnt_require_username(self):
        conjur_url = "https://conjur.example.com"
        connection_info = ConjurConnectionInfo(conjur_url, "some_account")

        credentials_provider = SimpleCredentialsProvider()
        # file deepcode ignore NoHardcodedCredentials/test: This is a test file
        # file deepcode ignore NoHardcodedPasswords/test: This is a test file
        credentials = CredentialsData(api_token="my_conjur_authn_token", machine=conjur_url)
        credentials_provider.save(credentials)
        
        provider = TokenAuthenticationStrategy(
            credentials_provider
        )

        res = await provider.authenticate(connection_info, None)
        self.assertIsNotNone(res)
        self.assertEqual(res[0], "my_conjur_authn_token")
        self.assertIsInstance(res[1], datetime)

    # TODO: Mock a conjur authn server and test that it is called with the correct parameters
