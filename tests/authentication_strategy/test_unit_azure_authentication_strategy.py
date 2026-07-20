from unittest.mock import AsyncMock, MagicMock, patch

from aiounittest import AsyncTestCase

from conjur_api.errors.errors import HttpStatusError, MissingRequiredParameterException
from conjur_api.http.endpoints import ConjurEndpoint
from conjur_api.models.general.conjur_connection_info import ConjurConnectionInfo
from conjur_api.providers.azure_authentication_strategy import (
    DEFAULT_IMDS_API_VERSION,
    DEFAULT_IMDS_BASE_URL,
    DEFAULT_RESOURCE_URI,
    IMDS_TOKEN_PATH,
    AzureAuthenticationStrategy,
)
from conjur_api.wrappers.http_wrapper import HttpVerb


class AzureAuthenticationStrategyTest(AsyncTestCase):

    def _make_strategy(self, identity="host/my-app/azure-host", **kwargs):
        return AzureAuthenticationStrategy(identity=identity, **kwargs)

    def _make_connection_info(self, service_id="my-service"):
        return ConjurConnectionInfo(
            conjur_url="https://conjur.example.com",
            account="myaccount",
            service_id=service_id,
        )

    # --- constructor ---

    def test_missing_identity_raises(self):
        with self.assertRaises(MissingRequiredParameterException):
            AzureAuthenticationStrategy(identity="")

    def test_missing_identity_whitespace_raises(self):
        with self.assertRaises(MissingRequiredParameterException):
            AzureAuthenticationStrategy(identity="   ")

    # --- _build_imds_url ---

    def test_build_imds_url_without_client_id(self):
        strategy = self._make_strategy()
        url = strategy._build_imds_url()
        assert f"{DEFAULT_IMDS_BASE_URL}{IMDS_TOKEN_PATH}" in url
        assert f"api-version={DEFAULT_IMDS_API_VERSION}" in url
        assert "resource=" in url
        assert "client_id" not in url

    def test_build_imds_url_with_client_id(self):
        strategy = self._make_strategy(client_id="my-client-id")
        url = strategy._build_imds_url()
        assert "client_id=my-client-id" in url

    def test_build_imds_url_custom_resource(self):
        strategy = self._make_strategy(resource_uri="https://vault.azure.net/")
        url = strategy._build_imds_url()
        assert "https%3A%2F%2Fvault.azure.net%2F" in url or "https://vault.azure.net/" in url

    # --- _fetch_azure_jwt error paths ---

    async def test_fetch_azure_jwt_raises_on_empty_token(self):
        strategy = self._make_strategy(imds_base_url="http://mock-imds")

        mock_response = AsyncMock()
        mock_response.ok = True
        mock_response.text = AsyncMock(return_value='{"access_token": ""}')

        mock_cm = AsyncMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_response)
        mock_cm.__aexit__ = AsyncMock(return_value=False)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_cm)

        mock_session_cm = AsyncMock()
        mock_session_cm.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_cm.__aexit__ = AsyncMock(return_value=False)

        with patch("conjur_api.providers.azure_authentication_strategy.ClientSession",
                   return_value=mock_session_cm):
            with self.assertRaises(MissingRequiredParameterException) as ctx:
                await strategy._fetch_azure_jwt()
        self.assertIn("empty access token", ctx.exception.message)

    async def test_fetch_azure_jwt_raises_on_http_error(self):
        strategy = self._make_strategy(imds_base_url="http://mock-imds")

        mock_response = AsyncMock()
        mock_response.ok = False
        mock_response.status = 400
        mock_response.text = AsyncMock(return_value='{"error": "bad request"}')

        mock_cm = AsyncMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_response)
        mock_cm.__aexit__ = AsyncMock(return_value=False)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_cm)

        mock_session_cm = AsyncMock()
        mock_session_cm.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_cm.__aexit__ = AsyncMock(return_value=False)

        with patch("conjur_api.providers.azure_authentication_strategy.ClientSession",
                   return_value=mock_session_cm):
            with self.assertRaises(HttpStatusError) as ctx:
                await strategy._fetch_azure_jwt()
        self.assertEqual(ctx.exception.status, 400)

    # --- service_id validation ---

    async def test_missing_service_id_raises(self):
        strategy = self._make_strategy()
        connection_info = self._make_connection_info(service_id=None)

        with patch.object(strategy, "_fetch_azure_jwt", new=AsyncMock(return_value="fake-jwt")):
            with self.assertRaises(MissingRequiredParameterException) as ctx:
                await strategy.authenticate(connection_info, None)
        self.assertIn("service_id", ctx.exception.message)

    # --- full authenticate happy path ---

    async def test_authenticate_calls_conjur_with_jwt(self):
        strategy = self._make_strategy(identity="host/my-app/azure-host")
        connection_info = self._make_connection_info(service_id="my-service")

        fake_jwt = "eyJhbGciOiJSUzI1NiJ9.fake"
        fake_token = '{"protected":"eyJ...","payload":"eyJ...","signature":"sig"}'

        mock_http_response = MagicMock()
        mock_http_response.text = fake_token

        with patch.object(strategy, "_fetch_azure_jwt", new=AsyncMock(return_value=fake_jwt)):
            with patch("conjur_api.providers.azure_authentication_strategy.invoke_endpoint",
                       new=AsyncMock(return_value=mock_http_response)) as mock_invoke:
                with patch("conjur_api.providers.azure_authentication_strategy.util_functions.calculate_token_expiration",
                           return_value="2099-01-01"):
                    token, expiry = await strategy.authenticate(connection_info, None)

        mock_invoke.assert_called_once_with(
            HttpVerb.POST,
            ConjurEndpoint.AUTHENTICATE_AZURE,
            {
                "url": "https://conjur.example.com",
                "service_id": "my-service",
                "account": "myaccount",
                "login": "host/my-app/azure-host",
            },
            f"jwt={fake_jwt}",
            ssl_verification_metadata=None,
            proxy_params=None,
        )
        self.assertEqual(token, fake_token)
        self.assertEqual(expiry, "2099-01-01")
