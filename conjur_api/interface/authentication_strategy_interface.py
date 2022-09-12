# -*- coding: utf-8 -*-

"""
AuthenticationStrategy Interface
This class describes a shared interface for authenticating to Conjur
"""

# Builtins
import abc
from datetime import datetime

from conjur_api.models.general.conjur_connection_info import ConjurConnectionInfo
from conjur_api.models.ssl.ssl_verification_metadata import SslVerificationMetadata

# pylint: disable=too-few-public-methods
class AuthenticationStrategyInterface(metaclass=abc.ABCMeta):  # pragma: no cover
    """
    AuthenticationStrategyInterface
    This class is an interface that outlines a shared interface for authentication strategies
    """

    @abc.abstractmethod
    async def authenticate(
        self,
        connection_info: ConjurConnectionInfo,
        ssl_verification_data: SslVerificationMetadata
    ) -> tuple[str, datetime]:
        """
        Authenticate uses the api_key to fetch a short-lived conjur_api token that
        for a limited time will allow you to interact fully with the Conjur
        vault.
        """
