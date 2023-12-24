"""
LdapAuthenticationStrategy module

This module holds the LdapAuthenticationStrategy class
"""

from conjur_api.errors.errors import MissingRequiredParameterException
from conjur_api.http.endpoints import ConjurEndpoint
from conjur_api.models.general.conjur_connection_info import ConjurConnectionInfo
from conjur_api.providers.authn_authentication_strategy import AuthnAuthenticationStrategy
from conjur_api.wrappers.http_wrapper import HttpVerb, invoke_endpoint

# pylint: disable=too-few-public-methods
class LdapAuthenticationStrategy(AuthnAuthenticationStrategy):
    """
    LdapAuthenticationStrategy class

    This class implements the "ldap" strategy of authentication. This is almost the same as
    AuthnAuthenticationStrategy, except that it uses the `service_id` field on `ConjurConnectionInfo`
    which is included in the authentication request url.
    """

    # pylint: disable=duplicate-code
    async def _send_login_request(self, ssl_verification_data, connection_info, creds):
        self._validate_service_id_exists(connection_info)

        params = {
            'url': connection_info.conjur_url,
            'service_id': connection_info.service_id,
            'account': connection_info.conjur_account,
        }

        response = await invoke_endpoint(HttpVerb.GET, ConjurEndpoint.LOGIN_LDAP,
                                         params, auth=(creds.username, creds.password),
                                         ssl_verification_metadata=ssl_verification_data,
                                         proxy_params=connection_info.proxy_params)

        return response.text

    async def _send_authenticate_request(self, ssl_verification_data, connection_info, creds):
        self._validate_service_id_exists(connection_info)

        params = {
            'url': connection_info.conjur_url,
            'service_id': connection_info.service_id,
            'account': connection_info.conjur_account,
            'login': creds.username,
        }

        response = await invoke_endpoint(
            HttpVerb.POST,
            ConjurEndpoint.AUTHENTICATE_LDAP,
            params,
            data=creds.api_key,
            ssl_verification_metadata=ssl_verification_data,
            proxy_params=connection_info.proxy_params)
        return response.text

    def _validate_service_id_exists(self, connection_info: ConjurConnectionInfo):
        if not connection_info.service_id:
            raise MissingRequiredParameterException("service_id is required for authn-ldap")
