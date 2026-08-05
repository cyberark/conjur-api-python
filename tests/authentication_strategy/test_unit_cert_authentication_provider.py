from unittest.mock import AsyncMock, patch, MagicMock
from aiounittest import AsyncTestCase

from conjur_api.errors.errors import MissingRequiredParameterException
from conjur_api.http.endpoints import ConjurEndpoint
from conjur_api.models.general.conjur_connection_info import ConjurConnectionInfo
from conjur_api.models.ssl.ssl_verification_metadata import SslVerificationMetadata
from conjur_api.models.ssl.ssl_verification_mode import SslVerificationMode
from conjur_api.providers import CertAuthenticationStrategy


MOCK_TOKEN = "eyJwcm90ZWN0ZWQiOiJleUpoYkdjaU9pSlNVekkxTmlKOSIsInBheWxvYWQiOiJleUp6ZFdJaU9pSjBaWE4wSW4wPSIsInNpZ25hdHVyZSI6InNpZyJ9"
CONJUR_URL = "https://conjur.example.com"
ACCOUNT = "test-account"
SERVICE_ID = "my-service"
CERT_FILE = "/path/to/cert.pem"
KEY_FILE = "/path/to/key.pem"
HOST_ID = "host/vm-workloads/vm-01"


class CertAuthenticationStrategyTest(AsyncTestCase):

    async def test_missing_service_id_raises(self):
        provider = CertAuthenticationStrategy(CERT_FILE, KEY_FILE, service_id="")
        connection_info = ConjurConnectionInfo(CONJUR_URL, ACCOUNT)
        ssl_data = SslVerificationMetadata(SslVerificationMode.TRUST_STORE)

        with self.assertRaises(MissingRequiredParameterException) as ctx:
            await provider.authenticate(connection_info, ssl_data)

        self.assertRegex(ctx.exception.message, "service_id is required")

    @patch("conjur_api.providers.cert_authentication_strategy.invoke_endpoint", new_callable=AsyncMock)
    async def test_request_mode_calls_correct_endpoint(self, mock_invoke):
        mock_response = MagicMock()
        mock_response.text = MOCK_TOKEN
        mock_invoke.return_value = mock_response

        provider = CertAuthenticationStrategy(CERT_FILE, KEY_FILE, SERVICE_ID, host_id=HOST_ID)
        connection_info = ConjurConnectionInfo(CONJUR_URL, ACCOUNT)
        ssl_data = SslVerificationMetadata(SslVerificationMode.TRUST_STORE)

        await provider.authenticate(connection_info, ssl_data)

        mock_invoke.assert_called_once()
        args = mock_invoke.call_args
        assert args[0][1] == ConjurEndpoint.AUTHENTICATE_CERT
        params = args[0][2]
        assert params['url'] == CONJUR_URL
        assert params['service_id'] == SERVICE_ID
        assert params['account'] == ACCOUNT
        # forward slashes in host_id must be percent-encoded
        assert params['login'] == "host%2Fvm-workloads%2Fvm-01"

    @patch("conjur_api.providers.cert_authentication_strategy.invoke_endpoint", new_callable=AsyncMock)
    async def test_spiffe_mode_calls_correct_endpoint(self, mock_invoke):
        mock_response = MagicMock()
        mock_response.text = MOCK_TOKEN
        mock_invoke.return_value = mock_response

        provider = CertAuthenticationStrategy(CERT_FILE, KEY_FILE, SERVICE_ID, host_id=None)
        connection_info = ConjurConnectionInfo(CONJUR_URL, ACCOUNT)
        ssl_data = SslVerificationMetadata(SslVerificationMode.TRUST_STORE)

        await provider.authenticate(connection_info, ssl_data)

        mock_invoke.assert_called_once()
        args = mock_invoke.call_args
        assert args[0][1] == ConjurEndpoint.AUTHENTICATE_CERT_SPIFFE
        params = args[0][2]
        assert 'login' not in params

    @patch("conjur_api.providers.cert_authentication_strategy.invoke_endpoint", new_callable=AsyncMock)
    async def test_client_cert_passed_in_ssl_metadata(self, mock_invoke):
        mock_response = MagicMock()
        mock_response.text = MOCK_TOKEN
        mock_invoke.return_value = mock_response

        provider = CertAuthenticationStrategy(CERT_FILE, KEY_FILE, SERVICE_ID, host_id=HOST_ID)
        connection_info = ConjurConnectionInfo(CONJUR_URL, ACCOUNT)
        ssl_data = SslVerificationMetadata(SslVerificationMode.TRUST_STORE)

        await provider.authenticate(connection_info, ssl_data)

        kwargs = mock_invoke.call_args[1]
        passed_ssl: SslVerificationMetadata = kwargs['ssl_verification_metadata']
        assert passed_ssl.client_cert_file == CERT_FILE
        assert passed_ssl.client_key_file == KEY_FILE

    @patch("conjur_api.providers.cert_authentication_strategy.invoke_endpoint", new_callable=AsyncMock)
    async def test_service_id_with_spaces_is_encoded(self, mock_invoke):
        mock_response = MagicMock()
        mock_response.text = MOCK_TOKEN
        mock_invoke.return_value = mock_response

        provider = CertAuthenticationStrategy(CERT_FILE, KEY_FILE, "my service", host_id=HOST_ID)
        connection_info = ConjurConnectionInfo(CONJUR_URL, ACCOUNT)
        ssl_data = SslVerificationMetadata(SslVerificationMode.TRUST_STORE)

        await provider.authenticate(connection_info, ssl_data)

        params = mock_invoke.call_args[0][2]
        assert params['service_id'] == "my%20service"

    @patch("conjur_api.providers.cert_authentication_strategy.invoke_endpoint", new_callable=AsyncMock)
    async def test_returns_token_and_expiration(self, mock_invoke):
        mock_response = MagicMock()
        mock_response.text = MOCK_TOKEN
        mock_invoke.return_value = mock_response

        provider = CertAuthenticationStrategy(CERT_FILE, KEY_FILE, SERVICE_ID, host_id=HOST_ID)
        connection_info = ConjurConnectionInfo(CONJUR_URL, ACCOUNT)
        ssl_data = SslVerificationMetadata(SslVerificationMode.TRUST_STORE)

        token, expiration = await provider.authenticate(connection_info, ssl_data)

        assert token == MOCK_TOKEN
        assert expiration is not None
