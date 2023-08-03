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
    OidcAuthenticationStrategy class

    This class implements the "oidc" strategy of authentication. This is almost the same as
    AuthnAuthenticationStrategy, except that it uses the `service_id` field on `ConjurConnectionInfo`
    which is included in the authentication request url.
    """

    # pylint: disable=duplicate-code
    async def _send_authenticate_request(self, ssl_verification_data, connection_info, creds):
        self._validate_service_id_exists(connection_info)

        params = {
            'url': connection_info.conjur_url,
            'service_id': connection_info.service_id,
            'account': connection_info.conjur_account,
        }

        if (not creds.code or not creds.code_verifier or not creds.nonce) and (not creds.username or not creds.password):
            raise MissingRequiredParameterException("code,code_verifier,nonce or username and password are required for login") 

        if not creds.code and creds.username and creds.password:
            data = f"id_token={creds.password}"
            response = await invoke_endpoint(HttpVerb.POST, ConjurEndpoint.AUTHENTICATE_OIDC,
                                         params, data, ssl_verification_metadata=ssl_verification_data)

        if creds.code and creds.code_verifier and creds.nonce:
            query = {
                'code': creds.code,
                'code_verifier': creds.code_verifier,
                'nonce': creds.nonce
            }
            response = await invoke_endpoint(HttpVerb.GET, ConjurEndpoint.AUTHENTICATE_OIDC,
                                         params, query=query, ssl_verification_metadata=ssl_verification_data)                                  
        return response.text

    async def _ensure_logged_in(self, connection_info, ssl_verification_data, creds):
        pass

    @staticmethod
    def _validate_service_id_exists(connection_info: ConjurConnectionInfo):
        if not connection_info.service_id:
            raise MissingRequiredParameterException("service_id is required for authn-oidc")
