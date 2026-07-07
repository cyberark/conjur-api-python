from unittest.mock import patch, MagicMock
from aiounittest import AsyncTestCase

from conjur_api.errors.errors import MissingRequiredParameterException
from conjur_api.http.endpoints import ConjurEndpoint
from conjur_api.models.general.conjur_connection_info import ConjurConnectionInfo
from conjur_api.models.general.credentials_data import CredentialsData, OidcCodeDetail
from conjur_api.models.ssl.ssl_verification_metadata import SslVerificationMetadata
from conjur_api.models.ssl.ssl_verification_mode import SslVerificationMode
from conjur_api.providers import OidcAuthenticationStrategy, SimpleCredentialsProvider
from conjur_api.wrappers.http_wrapper import HttpVerb


def _make_provider(code='mycode', code_verifier='myverifier', nonce='mynonce'):
    detail = OidcCodeDetail(code=code, code_verifier=code_verifier, nonce=nonce)
    creds = CredentialsData(machine='https://conjur', oidc_code_detail=detail)
    provider = SimpleCredentialsProvider()
    provider.save(creds)
    return OidcAuthenticationStrategy(provider)


class OidcAuthenticationStrategyTest(AsyncTestCase):

    async def test_missing_oidc_code_detail_raises(self):
        creds = CredentialsData(machine='https://conjur', username='user', password='pass')
        provider = SimpleCredentialsProvider()
        provider.save(creds)
        strategy = OidcAuthenticationStrategy(provider)
        connection_info = ConjurConnectionInfo('https://conjur', 'myaccount', service_id='svc')
        ssl_meta = SslVerificationMetadata(SslVerificationMode.INSECURE)

        with self.assertRaises(MissingRequiredParameterException):
            await strategy.authenticate(connection_info, ssl_meta)

    async def test_missing_code_raises(self):
        strategy = _make_provider(code=None)
        connection_info = ConjurConnectionInfo('https://conjur', 'myaccount', service_id='svc')
        ssl_meta = SslVerificationMetadata(SslVerificationMode.INSECURE)

        with self.assertRaises(MissingRequiredParameterException):
            await strategy.authenticate(connection_info, ssl_meta)

    async def test_missing_nonce_raises(self):
        strategy = _make_provider(nonce=None)
        connection_info = ConjurConnectionInfo('https://conjur', 'myaccount', service_id='svc')
        ssl_meta = SslVerificationMetadata(SslVerificationMode.INSECURE)

        with self.assertRaises(MissingRequiredParameterException):
            await strategy.authenticate(connection_info, ssl_meta)

    async def test_missing_code_verifier_raises(self):
        strategy = _make_provider(code_verifier=None)
        connection_info = ConjurConnectionInfo('https://conjur', 'myaccount', service_id='svc')
        ssl_meta = SslVerificationMetadata(SslVerificationMode.INSECURE)

        with self.assertRaises(MissingRequiredParameterException):
            await strategy.authenticate(connection_info, ssl_meta)

    @patch('conjur_api.providers.oidc_authentication_strategy.invoke_endpoint')
    async def test_sends_get_with_query_params(self, mock_invoke_endpoint):
        mock_response = MagicMock()
        mock_response.text = 'fake-api-token'
        mock_invoke_endpoint.return_value = mock_response

        strategy = _make_provider(code='c123', code_verifier='cv456', nonce='n789')
        connection_info = ConjurConnectionInfo('https://conjur', 'myaccount', service_id='test-svc')
        ssl_meta = SslVerificationMetadata(SslVerificationMode.INSECURE)

        await strategy.authenticate(connection_info, ssl_meta)

        args, kwargs = mock_invoke_endpoint.call_args
        self.assertEqual(args[0], HttpVerb.GET)
        self.assertEqual(args[1], ConjurEndpoint.AUTHENTICATE_OIDC)
        self.assertEqual(kwargs['query']['code'], 'c123')
        self.assertEqual(kwargs['query']['code_verifier'], 'cv456')
        self.assertEqual(kwargs['query']['nonce'], 'n789')
        mock_invoke_endpoint.assert_called_once()

    @patch('conjur_api.providers.oidc_authentication_strategy.invoke_endpoint')
    async def test_reused_code_raises(self, mock_invoke_endpoint):
        mock_response = MagicMock()
        mock_response.text = 'fake-api-token'
        mock_invoke_endpoint.return_value = mock_response

        strategy = _make_provider(code='c123', code_verifier='cv456', nonce='n789')
        connection_info = ConjurConnectionInfo('https://conjur', 'myaccount', service_id='test-svc')
        ssl_meta = SslVerificationMetadata(SslVerificationMode.INSECURE)

        await strategy.authenticate(connection_info, ssl_meta)

        with self.assertRaises(MissingRequiredParameterException):
            await strategy.authenticate(connection_info, ssl_meta)

    async def test_missing_service_id_raises(self):
        strategy = _make_provider()
        connection_info = ConjurConnectionInfo('https://conjur', 'myaccount')  # no service_id
        ssl_meta = SslVerificationMetadata(SslVerificationMode.INSECURE)

        with self.assertRaises(MissingRequiredParameterException):
            await strategy.authenticate(connection_info, ssl_meta)
