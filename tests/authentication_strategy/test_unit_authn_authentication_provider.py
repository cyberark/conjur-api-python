from aiounittest import AsyncTestCase

from conjur_api.errors.errors import MissingRequiredParameterException
from conjur_api.models.general.conjur_connection_info import ConjurConnectionInfo
from conjur_api.models.general.credentials_data import CredentialsData
from conjur_api.providers import AuthnAuthenticationStrategy
from conjur_api.providers.simple_credentials_provider import SimpleCredentialsProvider

class AuthnAuthenticationStrategyTest(AsyncTestCase):
    
    async def test_missing_username(self):
        conjur_url = "https://conjur.example.com"
        connection_info = ConjurConnectionInfo(conjur_url, "some_account")

        credentials_provider = SimpleCredentialsProvider()
        # file deepcode ignore NoHardcodedCredentials/test: This is a test file
        # file deepcode ignore NoHardcodedPasswords/test: This is a test file
        credentials = CredentialsData(password="mypassword", machine=conjur_url)
        credentials_provider.save(credentials)
        
        provider = AuthnAuthenticationStrategy(
            credentials_provider
        )
        with self.assertRaises(MissingRequiredParameterException) as context:
            await provider.authenticate(connection_info, None)

        self.assertRegex(context.exception.message, "Missing parameters")

    # TODO: Mock a conjur authn server and test that it is called with the correct parameters