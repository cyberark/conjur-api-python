import json
from unittest.mock import AsyncMock, MagicMock, patch

from aiounittest import AsyncTestCase

from conjur_api.errors.errors import MissingRequiredParameterException
from conjur_api.http.endpoints import ConjurEndpoint
from conjur_api.models.general.conjur_connection_info import ConjurConnectionInfo
from conjur_api.providers.aws_iam_authentication_strategy import (
    AWSIAMAuthenticationStrategy,
    build_signed_headers,
    is_valid_aws_region,
    is_valid_aws_host,
)
from conjur_api.wrappers.http_wrapper import HttpVerb


class AWSIAMAuthenticationStrategyTest(AsyncTestCase):

    def _make_strategy(self, identity="host/my-app/my-role", service_id="prod",
                       aws_region="us-east-1"):
        return AWSIAMAuthenticationStrategy(
            identity=identity, service_id=service_id, aws_region=aws_region
        )

    def _make_connection_info(self):
        return ConjurConnectionInfo(
            conjur_url="https://conjur.example.com",
            account="myaccount",
        )

    # --- constructor validation ---

    def test_missing_identity_raises(self):
        with self.assertRaises(MissingRequiredParameterException):
            AWSIAMAuthenticationStrategy(identity="")

    def test_whitespace_identity_raises(self):
        with self.assertRaises(MissingRequiredParameterException):
            AWSIAMAuthenticationStrategy(identity="   ")

    def test_missing_service_id_raises(self):
        with self.assertRaises(MissingRequiredParameterException):
            AWSIAMAuthenticationStrategy(identity="host/x", service_id="")

    def test_invalid_region_raises(self):
        with self.assertRaises(ValueError):
            AWSIAMAuthenticationStrategy(identity="host/x", aws_region="not-a-region")

    def test_global_region_accepted(self):
        s = AWSIAMAuthenticationStrategy(identity="host/x", aws_region="global")
        self.assertEqual(s.aws_region, "global")

    # --- is_valid_aws_region ---

    def test_valid_regions(self):
        for r in ["us-east-1", "us-west-2", "eu-central-1", "ap-southeast-2",
                  "us-gov-west-1", "us-isob-east-1", "me-central-1", "global"]:
            self.assertTrue(is_valid_aws_region(r), f"Expected {r!r} to be valid")

    def test_invalid_regions(self):
        for r in ["USEAST1", "us_east_1", "", "notaregion", "us-east-", "1-us-east"]:
            self.assertFalse(is_valid_aws_region(r), f"Expected {r!r} to be invalid")

    # --- is_valid_aws_host ---

    def test_valid_aws_host(self):
        self.assertTrue(is_valid_aws_host("sts.amazonaws.com"))
        self.assertTrue(is_valid_aws_host("sts.us-east-1.amazonaws.com"))

    def test_invalid_aws_host(self):
        self.assertFalse(is_valid_aws_host(None))
        self.assertFalse(is_valid_aws_host("evil.com"))
        self.assertFalse(is_valid_aws_host("amazonaws.com.evil.com"))

    # --- build_signed_headers ---

    def test_build_signed_headers_returns_json_with_authorization(self):
        mock_creds = MagicMock()
        mock_creds.access_key = "AKIAIOSFODNN7EXAMPLE"
        mock_creds.secret_key = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
        mock_creds.token = None

        mock_frozen = MagicMock()
        mock_frozen.access_key = mock_creds.access_key
        mock_frozen.secret_key = mock_creds.secret_key
        mock_frozen.token = None

        mock_session_creds = MagicMock()
        mock_session_creds.get_frozen_credentials.return_value = mock_frozen

        mock_session = MagicMock()
        mock_session.get_credentials.return_value = mock_session_creds

        with patch("conjur_api.providers.aws_iam_authentication_strategy.botocore.session.get_session",
                   return_value=mock_session):
            result = build_signed_headers("us-east-1")

        headers = json.loads(result)
        # botocore uses title-case header names
        self.assertIn("Authorization", headers)
        self.assertIn("X-Amz-Date", headers)
        self.assertIn("host", headers)

    def test_build_signed_headers_global_uses_sts_amazonaws_com(self):
        mock_frozen = MagicMock()
        mock_frozen.access_key = "AKID"
        mock_frozen.secret_key = "SECRET"
        mock_frozen.token = None

        mock_session_creds = MagicMock()
        mock_session_creds.get_frozen_credentials.return_value = mock_frozen

        mock_session = MagicMock()
        mock_session.get_credentials.return_value = mock_session_creds

        with patch("conjur_api.providers.aws_iam_authentication_strategy.botocore.session.get_session",
                   return_value=mock_session):
            result = build_signed_headers("global")

        headers = json.loads(result)
        self.assertEqual(headers["host"], "sts.amazonaws.com")

    # --- authenticate happy path ---

    async def test_authenticate_calls_conjur_with_signed_headers(self):
        strategy = self._make_strategy(identity="host/my-app/my-role", service_id="prod",
                                       aws_region="us-east-1")
        connection_info = self._make_connection_info()

        fake_headers_json = json.dumps({"Authorization": "AWS4-HMAC...", "host": "sts.amazonaws.com",
                                        "x-amz-date": "20240101T000000Z"})
        fake_token = '{"protected":"eyJ...","payload":"eyJ...","signature":"sig"}'

        mock_http_response = MagicMock()
        mock_http_response.text = fake_token

        with patch("conjur_api.providers.aws_iam_authentication_strategy.build_signed_headers",
                   return_value=fake_headers_json):
            with patch("conjur_api.providers.aws_iam_authentication_strategy.invoke_endpoint",
                       new=AsyncMock(return_value=mock_http_response)) as mock_invoke:
                with patch("conjur_api.providers.aws_iam_authentication_strategy.util_functions.calculate_token_expiration",
                           return_value="2099-01-01"):
                    token, expiry = await strategy.authenticate(connection_info, None)

        mock_invoke.assert_called_once_with(
            HttpVerb.POST,
            ConjurEndpoint.AUTHENTICATE_IAM,
            {
                "url": "https://conjur.example.com",
                "service_id": "prod",
                "account": "myaccount",
                "login": "host/my-app/my-role",
            },
            fake_headers_json,
            ssl_verification_metadata=None,
            proxy_params=None,
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(token, fake_token)
        self.assertEqual(expiry, "2099-01-01")
