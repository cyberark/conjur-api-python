# -*- coding: utf-8 -*-
"""
CertAuthenticationStrategy module

This module holds the CertAuthenticationStrategy class
"""

import logging
from datetime import datetime
from typing import Tuple
from urllib.parse import quote

from conjur_api.errors.errors import MissingRequiredParameterException
from conjur_api.http.endpoints import ConjurEndpoint
from conjur_api.interface import AuthenticationStrategyInterface
from conjur_api.models.general.conjur_connection_info import ConjurConnectionInfo
from conjur_api.models.ssl.ssl_verification_metadata import SslVerificationMetadata
from conjur_api.utils import util_functions
from conjur_api.wrappers.http_wrapper import HttpVerb, invoke_endpoint

logger = logging.getLogger(__name__)


class CertAuthenticationStrategy(AuthenticationStrategyInterface):
    """
    CertAuthenticationStrategy

    Authenticates to Conjur using mutual TLS (authn-cert). The client certificate
    is presented during the TLS handshake; an empty POST body is sent to the
    authn-cert endpoint to receive a Conjur API token.

    Two modes are supported:
    - Request mode: host_id is provided; Conjur validates the cert matches the host.
    - SPIFFE mode: host_id is None; Conjur derives the host from the cert's SPIFFE SAN URI.
    """

    def __init__(self, cert_file: str, key_file: str, service_id: str, host_id: str = None):
        """
        :param cert_file: Path to the PEM client certificate file.
        :param key_file: Path to the PEM private key file.
        :param service_id: The authn-cert service ID configured in Conjur.
        :param host_id: (optional) Conjur host ID (e.g. "host/workloads/vm-01").
                        If None, SPIFFE mode is used.
        """
        self.cert_file = cert_file
        self.key_file = key_file
        self.service_id = service_id
        self.host_id = host_id

    async def authenticate(
        self,
        connection_info: ConjurConnectionInfo,
        ssl_verification_data: SslVerificationMetadata,
    ) -> Tuple[str, datetime]:
        """
        Authenticate using the client certificate. Returns (api_token, expiration).
        """
        logger.debug("Authenticating via authn-cert to %s...", connection_info.conjur_url)

        if not self.service_id:
            raise MissingRequiredParameterException("service_id is required for authn-cert")

        ssl_with_client_cert = SslVerificationMetadata(
            mode=ssl_verification_data.mode,
            ca_cert_path=ssl_verification_data.ca_cert_path,
            client_cert_file=self.cert_file,
            client_key_file=self.key_file,
        )

        if self.host_id:
            endpoint = ConjurEndpoint.AUTHENTICATE_CERT
            params = {
                'url': connection_info.conjur_url,
                'service_id': quote(self.service_id, safe=''),
                'account': connection_info.conjur_account,
                'login': quote(self.host_id, safe=''),
            }
        else:
            endpoint = ConjurEndpoint.AUTHENTICATE_CERT_SPIFFE
            params = {
                'url': connection_info.conjur_url,
                'service_id': quote(self.service_id, safe=''),
                'account': connection_info.conjur_account,
            }

        response = await invoke_endpoint(
            HttpVerb.POST,
            endpoint,
            params,
            None,
            ssl_verification_metadata=ssl_with_client_cert,
            proxy_params=connection_info.proxy_params,
        )

        api_token = response.text
        return api_token, util_functions.calculate_token_expiration(api_token)
