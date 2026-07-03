"""
OidcAuthenticationStrategy module

This module holds the OidcAuthenticationStrategy class
"""

from conjur_api.errors.errors import MissingRequiredParameterException
from conjur_api.http.endpoints import ConjurEndpoint
from conjur_api.models.general.conjur_connection_info import ConjurConnectionInfo
from conjur_api.providers.authn_authentication_strategy import AuthnAuthenticationStrategy
from conjur_api.wrappers.http_wrapper import HttpVerb, invoke_endpoint


# pylint: disable=too-few-public-methods
class OidcAuthenticationStrategy(AuthnAuthenticationStrategy):
    """
    Implements OIDC v2 (authorization code + PKCE) authentication.

    Expects credentials to carry an OidcCodeDetail with code, code_verifier,
    and nonce obtained by:
      1. Calling GET /authn-oidc/{account}/providers to get server-generated nonce
         and code_verifier.
      2. Exchanging user credentials with the OIDC provider to obtain an
         authorization code.
    Then issues GET /authn-oidc/{service_id}/{account}/authenticate?code=...
    """

    _last_used_code = None

    async def _send_authenticate_request(self, ssl_verification_data, connection_info, creds):
        self._validate_service_id_exists(connection_info)

        oidc = creds.oidc_code_detail
        if not oidc:
            raise MissingRequiredParameterException(
                "oidc_code_detail with code, code_verifier, and nonce is required for authn-oidc"
            )
        if not oidc.code:
            raise MissingRequiredParameterException("code is required for authn-oidc")
        if not oidc.code_verifier:
            raise MissingRequiredParameterException("code_verifier is required for authn-oidc")
        if not oidc.nonce:
            raise MissingRequiredParameterException("nonce is required for authn-oidc")
        if oidc.code == self._last_used_code:
            raise MissingRequiredParameterException(
                "This OIDC authorization code was already used to authenticate. "
                "Authorization codes are single-use; obtain a new code and set it "
                "in oidc_code_detail before authenticating again."
            )

        params = {
            'url': connection_info.conjur_url,
            'service_id': connection_info.service_id,
            'account': connection_info.conjur_account,
        }
        query = {
            'code': oidc.code,
            'code_verifier': oidc.code_verifier,
            'nonce': oidc.nonce,
        }

        response = await invoke_endpoint(
            HttpVerb.GET,
            ConjurEndpoint.AUTHENTICATE_OIDC,
            params,
            query=query,
            ssl_verification_metadata=ssl_verification_data,
            proxy_params=connection_info.proxy_params,
        )
        self._last_used_code = oidc.code
        return response.text

    async def _ensure_logged_in(self, connection_info, ssl_verification_data, creds):
        pass

    @staticmethod
    def _validate_service_id_exists(connection_info: ConjurConnectionInfo):
        if not connection_info.service_id:
            raise MissingRequiredParameterException("service_id is required for authn-oidc")
