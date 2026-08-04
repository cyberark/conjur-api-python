# -*- coding: utf-8 -*-
"""
AzureAuthenticationStrategy module

This module holds the AzureAuthenticationStrategy class
"""

import json
import logging
from datetime import datetime
from typing import Optional, Tuple
from urllib.parse import urlencode

from aiohttp import ClientSession, ClientTimeout

from conjur_api.errors.errors import HttpStatusError, MissingRequiredParameterException
from conjur_api.http.endpoints import ConjurEndpoint
from conjur_api.interface import AuthenticationStrategyInterface
from conjur_api.models.general.conjur_connection_info import ConjurConnectionInfo
from conjur_api.models.ssl.ssl_verification_metadata import SslVerificationMetadata
from conjur_api.utils import util_functions
from conjur_api.wrappers.http_wrapper import HttpVerb, invoke_endpoint

logger = logging.getLogger(__name__)

IMDS_TOKEN_PATH = "/metadata/identity/oauth2/token"
DEFAULT_RESOURCE_URI = "https://management.azure.com/"
DEFAULT_IMDS_BASE_URL = "http://169.254.169.254"
DEFAULT_IMDS_API_VERSION = "2018-02-01"


class AzureAuthenticationStrategy(AuthenticationStrategyInterface):
    """
    AzureAuthenticationStrategy

    Authenticates to Conjur using an Azure Managed Identity JWT obtained from
    the Azure Instance Metadata Service (IMDS).
    """

    def __init__(
        self,
        identity: str,
        resource_uri: str = DEFAULT_RESOURCE_URI,
        client_id: Optional[str] = None,
        imds_base_url: str = DEFAULT_IMDS_BASE_URL,
        imds_api_version: str = DEFAULT_IMDS_API_VERSION,
    ):
        """
        :param identity: Conjur host identity, e.g. "host/my-app/azure-host"
        :param resource_uri: Azure resource URI for which the IMDS token is requested
        :param client_id: Optional client ID for a user-assigned managed identity
        :param imds_base_url: Override for the IMDS base URL (useful in tests)
        :param imds_api_version: Override for the IMDS API version
        """
        if not identity or not identity.strip():
            raise MissingRequiredParameterException("identity is required for authn-azure")
        self.identity = identity
        self.resource_uri = resource_uri
        self.client_id = client_id
        self.imds_base_url = imds_base_url
        self.imds_api_version = imds_api_version

    async def authenticate(
        self,
        connection_info: ConjurConnectionInfo,
        ssl_verification_data: SslVerificationMetadata,
    ) -> Tuple[str, datetime]:
        """
        Fetches an Azure JWT from IMDS then exchanges it for a Conjur token.
        """
        logger.debug("Authenticating to %s via authn-azure...", connection_info.conjur_url)
        azure_jwt = await self._fetch_azure_jwt()
        api_token = await self._exchange_jwt_for_conjur_token(azure_jwt, connection_info, ssl_verification_data)
        return api_token, util_functions.calculate_token_expiration(api_token)

    def _build_imds_url(self) -> str:
        query: dict = {
            "api-version": self.imds_api_version,
            "resource": self.resource_uri,
        }
        if self.client_id:
            query["client_id"] = self.client_id
        return f"{self.imds_base_url}{IMDS_TOKEN_PATH}?{urlencode(query)}"

    async def _fetch_azure_jwt(self) -> str:
        imds_url = self._build_imds_url()
        logger.debug("Fetching Azure JWT from IMDS: %s", imds_url)

        # trust_env=False: IMDS runs on a link-local address (169.254.169.254) that must
        # never be routed through a system proxy.
        async with ClientSession(trust_env=False, timeout=ClientTimeout(total=20)) as session:
            async with session.get(imds_url, headers={"Metadata": "true"}) as response:
                text = await response.text()
                if not response.ok:
                    raise HttpStatusError(
                        status=response.status,
                        message="Azure IMDS token request failed",
                        url=imds_url,
                        response=text,
                    )

        body = json.loads(text)
        access_token = body.get("access_token", "")
        if not access_token:
            raise MissingRequiredParameterException("Azure IMDS returned an empty access token")
        return access_token

    async def _exchange_jwt_for_conjur_token(
        self,
        azure_jwt: str,
        connection_info: ConjurConnectionInfo,
        ssl_verification_data: SslVerificationMetadata,
    ) -> str:
        self._validate_service_id_exists(connection_info)

        params = {
            "url": connection_info.conjur_url,
            "service_id": connection_info.service_id,
            "account": connection_info.conjur_account,
            "login": self.identity,
        }
        response = await invoke_endpoint(
            HttpVerb.POST,
            ConjurEndpoint.AUTHENTICATE_AZURE,
            params,
            f"jwt={azure_jwt}",
            ssl_verification_metadata=ssl_verification_data,
            proxy_params=connection_info.proxy_params,
        )
        return response.text

    def _validate_service_id_exists(self, connection_info: ConjurConnectionInfo) -> None:
        if not connection_info.service_id:
            raise MissingRequiredParameterException("service_id is required for authn-azure")
