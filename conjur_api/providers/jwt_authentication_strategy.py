# -*- coding: utf-8 -*-
"""
JWTAuthenticationStrategy module

This module holds the JWTAuthenticationStrategy class
"""

import logging
from datetime import datetime
from typing import Tuple

from conjur_api.errors.errors import MissingRequiredParameterException
from conjur_api.http.endpoints import ConjurEndpoint
from conjur_api.interface import AuthenticationStrategyInterface
from conjur_api.models.general.conjur_connection_info import \
    ConjurConnectionInfo
from conjur_api.models.ssl.ssl_verification_metadata import \
    SslVerificationMetadata
from conjur_api.utils import util_functions
from conjur_api.wrappers.http_wrapper import HttpVerb, invoke_endpoint

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

        return api_token, util_functions.calculate_token_expiration(api_token)

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
