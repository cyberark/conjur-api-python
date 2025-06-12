"""
Authentication Strategy for using a pre-existing API access token
"""

# pylint: disable=missing-function-docstring

import logging
from datetime import datetime
from typing import Tuple

from conjur_api.errors.errors import MissingRequiredParameterException
from conjur_api.interface import AuthenticationStrategyInterface
from conjur_api.interface.credentials_store_interface import \
    CredentialsProviderInterface
from conjur_api.models.general.conjur_connection_info import \
    ConjurConnectionInfo
from conjur_api.models.general.credentials_data import CredentialsData
from conjur_api.models.ssl.ssl_verification_metadata import \
    SslVerificationMetadata
from conjur_api.utils import util_functions

logger = logging.getLogger(__name__)


class TokenAuthenticationStrategy(AuthenticationStrategyInterface):
    """
    Authentication strategy that uses a pre-existing API access token for authentication.
    This bypasses the login flow and allows direct access to Conjur using an existing token.
    """

    def __init__(self, credentials_provider: CredentialsProviderInterface):
        """
        Initialize a TokenAuthenticationStrategy with the provided token.

        Args:
            token: The authentication token to use.
        """
        self._credentials_provider = credentials_provider

    async def authenticate(
        self,
        connection_info: ConjurConnectionInfo,
        _ssl_verification_data: SslVerificationMetadata
    ) -> Tuple[str, datetime]:
        """
        Returns the pre-existing token for authentication along with its expiration.
        This method does not contact the Conjur server. The arguments are present
        to match the interface but are not used in this strategy.

        Returns:
            A tuple containing the token and its expiration datetime.
        """

        creds = self._retrieve_credential_data(connection_info.conjur_url)

        if not creds.api_token:
            raise MissingRequiredParameterException("authn token is missing")

        expiration = util_functions.calculate_token_expiration(creds.api_token)
        return creds.api_token, expiration

    def _retrieve_credential_data(self, url: str) -> CredentialsData:
        credential_location = self._credentials_provider.get_store_location()
        logger.debug("Retrieving credentials from the '%s'...", credential_location)

        return self._credentials_provider.load(url)
