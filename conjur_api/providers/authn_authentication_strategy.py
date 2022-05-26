"""
AuthnAuthenticationStrategy module

This module holds the AuthnAuthenticationStrategy class
"""

import logging
from conjur_api.errors.errors import MissingRequiredParameterException
from conjur_api.http.endpoints import ConjurEndpoint
from conjur_api.interface.authentication_strategy_interface import AuthenticationStrategyInterface
from conjur_api.interface.credentials_store_interface import CredentialsProviderInterface
from conjur_api.models.general.conjur_connection_info import ConjurConnectionInfo
from conjur_api.models.general.credentials_data import CredentialsData
from conjur_api.models.ssl.ssl_verification_metadata import SslVerificationMetadata
from conjur_api.wrappers.http_wrapper import HttpVerb, invoke_endpoint

class AuthnAuthenticationStrategy(AuthenticationStrategyInterface):
    """
    AuthnAuthenticationStrategy class

    This class implements the "authn" strategy of authentication, which is Conjur's default authenticator type.
    """
    def __init__(
            self,
            credentials_provider: CredentialsProviderInterface,
    ):
        self._credentials_provider = credentials_provider
        self._api_key = None

    async def login(self, connection_info: ConjurConnectionInfo, ssl_verification_data: SslVerificationMetadata) -> str:
        """
        Login uses a username and password to fetch a long-lived conjur_api token
        """

        logging.debug("Logging in to %s...", connection_info.conjur_url)
        creds = self._retrieve_credential_data(connection_info.conjur_url)

        if not creds.password:
            raise MissingRequiredParameterException("password is required for login")

        self._api_key = await self._send_login_request(ssl_verification_data, connection_info, creds)
        return self._api_key

    async def authenticate(self, connection_info, ssl_verification_data) -> str:
        """
        Authenticate uses the api_key (retrieved in `login()`) to fetch a short-lived conjur_api token that
        for a limited time will allow you to interact fully with the Conjur vault.
        """
        logging.debug("Authenticating to %s...", connection_info.conjur_url)
        creds = self._retrieve_credential_data(connection_info.conjur_url)
        await self._ensure_logged_in(connection_info, ssl_verification_data, creds)
        return await self._send_authenticate_request(ssl_verification_data, connection_info, creds)

    def _retrieve_credential_data(self, url: str) -> CredentialsData:
        credential_location = self._credentials_provider.get_store_location()
        logging.debug("Retrieving credentials from the '%s'...", credential_location)

        return self._credentials_provider.load(url)

    async def _ensure_logged_in(self, connection_info, ssl_verification_data, creds):
        if not self._api_key and creds.username and creds.password:
            # TODO we do this since api_key is not provided. it should be stored like username,
            # password inside credentials_data
            await self.login(connection_info, ssl_verification_data)

        if not creds.username or not self._api_key:
            raise MissingRequiredParameterException("Missing parameters in "
                                                    "authentication invocation")

    async def _send_login_request(self, ssl_verification_data, connection_info, creds):
        params = {
            'url': connection_info.conjur_url,
            'account': connection_info.conjur_account
        }

        response = await invoke_endpoint(HttpVerb.GET, ConjurEndpoint.LOGIN,
                                         params, auth=(creds.username, creds.password),
                                         ssl_verification_metadata=ssl_verification_data)

        return response.text

    async def _send_authenticate_request(self, ssl_verification_data, connection_info, creds):
        params = {
            'url': connection_info.conjur_url,
            'account': connection_info.conjur_account,
            'login': creds.username
        }

        response = await invoke_endpoint(
            HttpVerb.POST,
            ConjurEndpoint.AUTHENTICATE,
            params,
            self._api_key,
            ssl_verification_metadata=ssl_verification_data)
        return response.text
