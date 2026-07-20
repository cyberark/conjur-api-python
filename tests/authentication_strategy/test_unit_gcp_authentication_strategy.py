import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiounittest import AsyncTestCase

from conjur_api.errors.errors import HttpStatusError, MissingRequiredParameterException
from conjur_api.http.endpoints import ConjurEndpoint
from conjur_api.models.general.conjur_connection_info import ConjurConnectionInfo
from conjur_api.providers.gcp_authentication_strategy import (
    GCPAuthenticationStrategy,
    GCP_METADATA_FLAVOR_HEADER,
    GCP_METADATA_FLAVOR_VALUE,
)
from conjur_api.wrappers.http_wrapper import HttpVerb


class GCPAuthenticationStrategyTest(AsyncTestCase):

    def _make_strategy(self, identity="host/data/test/gcp-apps/test-app", jwt=None):
        return GCPAuthenticationStrategy(identity=identity, jwt=jwt)

    def _make_connection_info(self, service_id="gcp"):
        return ConjurConnectionInfo(
            conjur_url="https://conjur.example.com",
            account="myaccount",
            service_id=service_id,
        )

    # --- constructor validation ---

    def test_missing_identity_raises(self):
        with self.assertRaises(MissingRequiredParameterException):
            GCPAuthenticationStrategy(identity="")

    def test_whitespace_identity_raises(self):
        with self.assertRaises(MissingRequiredParameterException):
            GCPAuthenticationStrategy(identity="   ")

    # --- _build_metadata_url ---

    def test_build_metadata_url_strips_host_prefix(self):
        s = self._make_strategy(identity="host/data/test/gcp-apps/test-app")
        url = s._build_metadata_url("myaccount")
        assert "audience=conjur%2Fmyaccount%2Fhost%2Fdata%2Ftest%2Fgcp-apps%2Ftest-app" in url
        assert "format=full" in url
        assert s.gcp_identity_url in url

    def test_build_metadata_url_without_host_prefix(self):
        s = self._make_strategy(identity="data/test/gcp-apps/test-app")
        url = s._build_metadata_url("myaccount")
        assert "audience=conjur%2Fmyaccount%2Fhost%2Fdata%2Ftest%2Fgcp-apps%2Ftest-app" in url

    # --- _fetch_gcp_jwt ---

    async def test_fetch_gcp_jwt_returns_token(self):
        fake_token = "header.payload.signature"

        mock_response = AsyncMock()
        mock_response.ok = True
        mock_response.text = AsyncMock(return_value=fake_token)
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=False)

        mock_session = AsyncMock()
        mock_session.get = MagicMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        s = self._make_strategy()
        with patch(
            "conjur_api.providers.gcp_authentication_strategy.ClientSession",
            return_value=mock_session,
        ):
            result = await s._fetch_gcp_jwt("myaccount")

        assert result == fake_token
        call_kwargs = mock_session.get.call_args
        headers = call_kwargs[1]["headers"]
        assert headers[GCP_METADATA_FLAVOR_HEADER] == GCP_METADATA_FLAVOR_VALUE

    async def test_fetch_gcp_jwt_raises_on_http_error(self):
        mock_response = AsyncMock()
        mock_response.ok = False
        mock_response.status = 404
        mock_response.text = AsyncMock(return_value="not found")
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=False)

        mock_session = AsyncMock()
        mock_session.get = MagicMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        s = self._make_strategy()
        with patch(
            "conjur_api.providers.gcp_authentication_strategy.ClientSession",
            return_value=mock_session,
        ):
            with self.assertRaises(HttpStatusError):
                await s._fetch_gcp_jwt("myaccount")

    async def test_fetch_gcp_jwt_raises_on_empty_body(self):
        mock_response = AsyncMock()
        mock_response.ok = True
        mock_response.text = AsyncMock(return_value="   ")
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=False)

        mock_session = AsyncMock()
        mock_session.get = MagicMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        s = self._make_strategy()
        with patch(
            "conjur_api.providers.gcp_authentication_strategy.ClientSession",
            return_value=mock_session,
        ):
            with self.assertRaises(MissingRequiredParameterException):
                await s._fetch_gcp_jwt("myaccount")

    # --- authenticate ---

    async def test_authenticate_uses_explicit_jwt_without_metadata_call(self):
        fake_jwt = "header.payload.signature"
        fake_token = '{"protected":"eyJ...","payload":"eyJ...","signature":"sig"}'

        mock_http_response = MagicMock()
        mock_http_response.text = fake_token

        strategy = GCPAuthenticationStrategy(
            identity="host/data/test/gcp-apps/test-app",
            jwt=fake_jwt,
        )
        connection_info = self._make_connection_info()

        with patch(
            "conjur_api.providers.gcp_authentication_strategy.invoke_endpoint",
            new=AsyncMock(return_value=mock_http_response),
        ) as mock_invoke:
            with patch(
                "conjur_api.providers.gcp_authentication_strategy.util_functions.calculate_token_expiration",
                return_value="2099-01-01",
            ):
                token, expiry = await strategy.authenticate(connection_info, None)

        mock_invoke.assert_called_once_with(
            HttpVerb.POST,
            ConjurEndpoint.AUTHENTICATE_GCP,
            {
                "url": "https://conjur.example.com",
                "service_id": "gcp",
                "account": "myaccount",
                "login": "host/data/test/gcp-apps/test-app",
            },
            f"jwt={fake_jwt}",
            ssl_verification_metadata=None,
            proxy_params=None,
        )
        assert token == fake_token
        assert expiry == "2099-01-01"

    async def test_authenticate_fetches_jwt_when_not_provided(self):
        fake_jwt = "fetched.jwt.token"
        fake_token = '{"protected":"eyJ...","payload":"eyJ...","signature":"sig"}'

        mock_http_response = MagicMock()
        mock_http_response.text = fake_token

        strategy = self._make_strategy()
        connection_info = self._make_connection_info()

        with patch.object(strategy, "_fetch_gcp_jwt", new=AsyncMock(return_value=fake_jwt)):
            with patch(
                "conjur_api.providers.gcp_authentication_strategy.invoke_endpoint",
                new=AsyncMock(return_value=mock_http_response),
            ):
                with patch(
                    "conjur_api.providers.gcp_authentication_strategy.util_functions.calculate_token_expiration",
                    return_value="2099-01-01",
                ):
                    token, expiry = await strategy.authenticate(connection_info, None)

        assert token == fake_token

    async def test_authenticate_raises_without_service_id(self):
        strategy = GCPAuthenticationStrategy(
            identity="host/data/test/gcp-apps/test-app",
            jwt="fake.jwt.token",
        )
        connection_info = self._make_connection_info(service_id=None)

        with self.assertRaises(MissingRequiredParameterException):
            await strategy.authenticate(connection_info, None)
