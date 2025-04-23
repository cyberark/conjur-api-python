# -*- coding: utf-8 -*-
"""
JWTAuthenticationStrategy module

This module holds the JWTAuthenticationStrategy class
"""

import base64
import json
import logging
from datetime import datetime, timedelta
from typing import Tuple

from conjur_api.errors.errors import MissingRequiredParameterException
from conjur_api.http.endpoints import ConjurEndpoint
from conjur_api.interface import AuthenticationStrategyInterface
from conjur_api.models.general.conjur_connection_info import \
    ConjurConnectionInfo
from conjur_api.models.ssl.ssl_verification_metadata import \
    SslVerificationMetadata
from conjur_api.wrappers.http_wrapper import HttpVerb, invoke_endpoint

# Tokens should only be reused for 5 minutes (max lifetime is 8 minutes)
DEFAULT_TOKEN_EXPIRATION = 8
API_TOKEN_SAFETY_BUFFER = 3
DEFAULT_API_TOKEN_DURATION = DEFAULT_TOKEN_EXPIRATION - API_TOKEN_SAFETY_BUFFER

logger = logging.getLogger(__name__)

class JWTAuthenticationStrategy(AuthenticationStrategyInterface):
    """
    JWTAuthenticationStrategy

    This class makes an HTTP POST request to authenticate and retrieve a token.
    """

    def __init__(self, jwt_token: str):
        """
        Initializes the JWTAuthenticationStrategy with a JWT token.

        :param jwt_token: The JWT token to authenticate with
        """
        self.jwt_token = jwt_token  # Store JWT token in the class

    async def authenticate(
        self,
        connection_info: ConjurConnectionInfo,
        ssl_verification_data: SslVerificationMetadata,
    ) -> Tuple[str, datetime]:
        """
        Authenticate method makes a POST request to the authentication endpoint,
        retrieves a token, and calculates the token expiration.
        """
        logger.debug("Authenticating to %s...", connection_info.conjur_url)

        api_token = await self._send_authenticate_request(ssl_verification_data, connection_info)

        return api_token, self._calculate_token_expiration(api_token)

    async def _send_authenticate_request(self, ssl_verification_data, connection_info):
        self._validate_service_id_exists(connection_info)

        params = {
            'url': connection_info.conjur_url,
            'service_id': connection_info.service_id,
            'account': connection_info.conjur_account,
        }
        data = f"jwt={self.jwt_token}"

        response = await invoke_endpoint(
            HttpVerb.POST,
            ConjurEndpoint.AUTHENTICATE_JWT,
            params,
            data,
            ssl_verification_metadata=ssl_verification_data,
            proxy_params=connection_info.proxy_params)
        return response.text

    def _validate_service_id_exists(self, connection_info: ConjurConnectionInfo):
        if not connection_info.service_id:
            raise MissingRequiredParameterException("service_id is required for authn-jwt")

    @staticmethod
    # pylint: disable=bare-except
    def _calculate_token_expiration(api_token: str) -> datetime:
        """
        Calculate the expiration of the token by decoding the payload and extracting 'exp'.
        """
        try:
            # The token is in JSON format. Each field in the token is base64 encoded.
            # Decode the payload field and extract the expiration date.
            decoded_token_payload = base64.b64decode(json.loads(api_token)['payload'].encode('ascii'))
            token_expiration = json.loads(decoded_token_payload)['exp']
            return datetime.fromtimestamp(token_expiration) - timedelta(minutes=API_TOKEN_SAFETY_BUFFER)
        except:
            # If we can't extract the expiration from the token, fall back to the default expiration
            return datetime.now() + timedelta(minutes=DEFAULT_API_TOKEN_DURATION)
