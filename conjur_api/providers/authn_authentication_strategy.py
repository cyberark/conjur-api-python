"""
AuthnAuthenticationStrategy module

This module holds the AuthnAuthenticationStrategy class
"""
import base64
import json
import logging
from datetime import datetime, timedelta

from conjur_api.errors.errors import MissingRequiredParameterException
from conjur_api.http.endpoints import ConjurEndpoint
from conjur_api.interface.authentication_strategy_interface import AuthenticationStrategyInterface
from conjur_api.interface.credentials_store_interface import CredentialsProviderInterface
from conjur_api.models.general.conjur_connection_info import ConjurConnectionInfo
from conjur_api.models.general.credentials_data import CredentialsData
from conjur_api.models.ssl.ssl_verification_metadata import SslVerificationMetadata
from conjur_api.wrappers.http_wrapper import HttpVerb, invoke_endpoint

# Tokens should only be reused for 5 minutes (max lifetime is 8 minutes)
DEFAULT_TOKEN_EXPIRATION = 8
API_TOKEN_SAFETY_BUFFER = 3
DEFAULT_API_TOKEN_DURATION = DEFAULT_TOKEN_EXPIRATION - API_TOKEN_SAFETY_BUFFER


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

    async def login(self, connection_info: ConjurConnectionInfo, ssl_verification_data: SslVerificationMetadata) -> str:
        """
        Login uses a username and password to fetch a long-lived conjur_api token
        """

        logging.debug("Logging in to %s...", connection_info.conjur_url)
        creds = self._retrieve_credential_data(connection_info.conjur_url)

        if not creds.password:
            raise MissingRequiredParameterException("password is required for login")

        creds.api_key = await self._send_login_request(ssl_verification_data, connection_info, creds)
        return creds.api_key

    async def authenticate(self, connection_info, ssl_verification_data) -> tuple[str, datetime]:
        """
        Authenticate uses the api_key (retrieved in `login()`) to fetch a short-lived conjur_api token that
        for a limited time will allow you to interact fully with the Conjur vault.
        """
        logging.debug("Authenticating to %s...", connection_info.conjur_url)
        creds = self._retrieve_credential_data(connection_info.conjur_url)

        # If the credential provider already has a valid API token, return it
        if self._is_authenticated(creds):
            return str(creds.api_token), creds.api_token_expiration_datetime()

        await self._ensure_logged_in(connection_info, ssl_verification_data, creds)
        api_token = await self._send_authenticate_request(ssl_verification_data, connection_info, creds)

        return api_token, self._calculate_token_expiration(api_token)

    def _retrieve_credential_data(self, url: str) -> CredentialsData:
        credential_location = self._credentials_provider.get_store_location()
        logging.debug("Retrieving credentials from the '%s'...", credential_location)

        return self._credentials_provider.load(url)

    async def _ensure_logged_in(self, connection_info, ssl_verification_data, creds):
        if not creds.api_key and creds.username and creds.password:
            creds.api_key = await self.login(connection_info, ssl_verification_data)

        if not creds.username or not creds.api_key:
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
            creds.api_key,
            ssl_verification_metadata=ssl_verification_data)
        return response.text

    @staticmethod
    def _is_authenticated(creds) -> bool:
        if creds.api_token and creds.api_token_expiration:
            return creds.api_token_expiration_datetime() > datetime.now()
        return False

    @staticmethod
    # pylint: disable=bare-except
    def _calculate_token_expiration(api_token: str) -> datetime:
        # Attempt to get the expiration from the token. If failing then the default expiration will be used
        try:
            # The token is in JSON format. Each field in the token is base64 encoded.
            # So we decode the payload filed and then extract the expiration date from it
            decoded_token_payload = base64.b64decode(json.loads(api_token)['payload'].encode('ascii'))
            token_expiration = json.loads(decoded_token_payload)['exp']
            return datetime.fromtimestamp(token_expiration) - timedelta(minutes=API_TOKEN_SAFETY_BUFFER)
        except:
            # If we can't extract the expiration from the token because we work with an older version
            # of Conjur, then we use the default expiration
            return datetime.now() + timedelta(minutes=DEFAULT_API_TOKEN_DURATION)
