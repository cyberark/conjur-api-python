# -*- coding: utf-8 -*-
"""
GCPAuthenticationStrategy module

This module holds the GCPAuthenticationStrategy class
"""

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

GCP_METADATA_FLAVOR_HEADER = "Metadata-Flavor"
GCP_METADATA_FLAVOR_VALUE = "Google"
DEFAULT_GCP_IDENTITY_URL = (
    "http://metadata.google.internal/computeMetadata/v1"
    "/instance/service-accounts/default/identity"
)


class GCPAuthenticationStrategy(AuthenticationStrategyInterface):
    """
    GCPAuthenticationStrategy

    Authenticates to Conjur using a GCP identity token obtained from the
    GCP Instance Metadata Service, then exchanged via the authn-jwt/gcp endpoint.
    An explicit JWT may be supplied to bypass the metadata service fetch.
    """

    def __init__(
        self,
        identity: str,
        jwt: Optional[str] = None,
        gcp_identity_url: str = DEFAULT_GCP_IDENTITY_URL,
    ):
        """
        :param identity: Conjur host identity, e.g. "host/data/test/gcp-apps/test-app"
        :param jwt: Optional pre-obtained GCP identity token. When supplied the metadata
                    service is not called (useful in tests and CI where the token is
                    pre-fetched on a GCP agent and passed via environment variable).
        :param gcp_identity_url: Override for the GCP metadata identity URL (for testing)
        """
        if not identity or not identity.strip():
            raise MissingRequiredParameterException("identity is required for authn-jwt/gcp")
        self.identity = identity
        self.jwt = jwt
        self.gcp_identity_url = gcp_identity_url

    async def authenticate(
        self,
        connection_info: ConjurConnectionInfo,
        ssl_verification_data: SslVerificationMetadata,
    ) -> Tuple[str, datetime]:
        logger.debug("Authenticating to %s via authn-jwt/gcp...", connection_info.conjur_url)
        gcp_jwt = self.jwt or await self._fetch_gcp_jwt(connection_info.conjur_account)
        api_token = await self._exchange_jwt_for_conjur_token(
            gcp_jwt, connection_info, ssl_verification_data
        )
        return api_token, util_functions.calculate_token_expiration(api_token)

    def _build_metadata_url(self, account: str) -> str:
        normalized = (
            self.identity[len("host/"):]
            if self.identity.startswith("host/")
            else self.identity
        )
        audience = f"conjur/{account}/host/{normalized}"
        return f"{self.gcp_identity_url}?{urlencode({'audience': audience, 'format': 'full'})}"

    async def _fetch_gcp_jwt(self, account: str) -> str:
        metadata_url = self._build_metadata_url(account)
        logger.debug("Fetching GCP identity token from metadata service: %s", metadata_url)

        # trust_env=False: metadata server runs on a link-local address that must
        # never be routed through a system proxy.
        async with ClientSession(trust_env=False, timeout=ClientTimeout(total=20)) as session:
            async with session.get(
                metadata_url,
                headers={GCP_METADATA_FLAVOR_HEADER: GCP_METADATA_FLAVOR_VALUE},
            ) as response:
                body = await response.text()
                if not response.ok:
                    raise HttpStatusError(
                        status=response.status,
                        message="GCP metadata token request failed",
                        url=metadata_url,
                        response=body,
                    )

        if not body or not body.strip():
            raise MissingRequiredParameterException(
                "GCP metadata service returned an empty token"
            )
        return body.strip()

    async def _exchange_jwt_for_conjur_token(
        self,
        gcp_jwt: str,
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
            ConjurEndpoint.AUTHENTICATE_GCP,
            params,
            f"jwt={gcp_jwt}",
            ssl_verification_metadata=ssl_verification_data,
            proxy_params=connection_info.proxy_params,
        )
        return response.text

    def _validate_service_id_exists(self, connection_info: ConjurConnectionInfo) -> None:
        if not connection_info.service_id:
            raise MissingRequiredParameterException("service_id is required for authn-jwt/gcp")
