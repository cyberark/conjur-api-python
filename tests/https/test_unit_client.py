from unittest import IsolatedAsyncioTestCase

from asynctest import patch

from conjur_api import Client
from conjur_api.errors.errors import HttpError
from conjur_api.models import ConjurConnectionInfo, CredentialsData, SslVerificationMode
from conjur_api.providers import SimpleCredentialsProvider
from tests.https.common import MockResponse


class ClientTest(IsolatedAsyncioTestCase):

    @patch('aiohttp.ClientSession.request')
    async def test_client_enable_valid_authenticator(self, mock_request):
        conjur_data, credentials_provider = self._initialize_input()

        mock_request.return_value = MockResponse('', 204)
        c = Client(conjur_data, credentials_provider=credentials_provider, ssl_verification_mode=SslVerificationMode.INSECURE)
        response = await c.set_authenticator_state('authn-iam/test', True)

        self.assertTrue(response == '')

    @patch('aiohttp.ClientSession.request')
    async def test_client_disable_valid_authenticator(self, mock_request):
        conjur_data, credentials_provider = self._initialize_input()

        mock_request.return_value = MockResponse('', 204)
        c = Client(conjur_data, credentials_provider=credentials_provider, ssl_verification_mode=SslVerificationMode.INSECURE)
        response = await c.set_authenticator_state('authn-iam/test', False)

        self.assertTrue(response == '')

    @patch('aiohttp.ClientSession.request')
    async def test_client_enable_authenticator_no_permissions(self, mock_request):
        conjur_data, credentials_provider = self._initialize_input()

        mock_request.return_value = MockResponse('', 403)
        c = Client(conjur_data, credentials_provider=credentials_provider, ssl_verification_mode=SslVerificationMode.INSECURE)

        with self.assertRaises(HttpError) as context:
            await c.set_authenticator_state('authn-iam/test', True)

    @patch('aiohttp.ClientSession.request')
    async def test_client_disable_authenticator_no_permissions(self, mock_request):
        conjur_data, credentials_provider = self._initialize_input()

        mock_request.return_value = MockResponse('', 403)
        c = Client(conjur_data, credentials_provider=credentials_provider, ssl_verification_mode=SslVerificationMode.INSECURE)

        with self.assertRaises(HttpError) as context:
            await c.set_authenticator_state('authn-iam/test', False)

    @patch('aiohttp.ClientSession.request')
    async def test_client_enable_non_existing_authenticator(self, mock_request):
        conjur_data, credentials_provider = self._initialize_input()

        mock_request.return_value = MockResponse('', 401)
        c = Client(conjur_data, credentials_provider=credentials_provider, ssl_verification_mode=SslVerificationMode.INSECURE)

        with self.assertRaises(HttpError) as context:
            await c.set_authenticator_state('authn-iam/test', True)

    @patch('aiohttp.ClientSession.request')
    async def test_client_disable_non_existing_authenticator(self, mock_request):
        conjur_data, credentials_provider = self._initialize_input()

        mock_request.return_value = MockResponse('', 401)
        c = Client(conjur_data, credentials_provider=credentials_provider, ssl_verification_mode=SslVerificationMode.INSECURE)

        with self.assertRaises(HttpError) as context:
            await c.set_authenticator_state('authn-iam/test', False)

    @staticmethod
    def _initialize_input() -> tuple[ConjurConnectionInfo, SimpleCredentialsProvider]:
        conjur_url = 'https://conjur-https'
        conjur_data = ConjurConnectionInfo(
            conjur_url=conjur_url,
            account='dev'
        )
        credentials_provider = SimpleCredentialsProvider()
        credentials = CredentialsData(username='user', password='password', machine=conjur_url)
        credentials_provider.save(credentials)

        return conjur_data, credentials_provider
