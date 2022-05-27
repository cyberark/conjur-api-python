"""
SimpleCredentialsProvider module

This module holds the SimpleCredentialsProvider class
"""
from copy import deepcopy
from typing import Dict

from conjur_api.interface import CredentialsProviderInterface
from conjur_api.models import CredentialsData


class SimpleCredentialsProvider(CredentialsProviderInterface):
    """
    SimpleCredentialsProvider class

    This class implement a naive, in-memory implementation of the CredentialsProvider Interface
    """

    def __init__(self):
        self._credentials: Dict[str, CredentialsData] = {}

    def save(self, credential_data: CredentialsData):
        self._credentials[credential_data.machine] = deepcopy(credential_data)

    def load(self, conjur_url: str) -> CredentialsData:
        return self._credentials[conjur_url]

    def update_api_key_entry(self, user_to_update: str, credential_data: CredentialsData, new_api_key: str):
        pass

    def remove_credentials(self, conjur_url: str):
        del self._credentials[conjur_url]

    def is_exists(self, conjur_url: str) -> bool:
        return conjur_url in self._credentials

    def cleanup_if_exists(self, conjur_url: str):
        if self.is_exists(conjur_url):
            self.remove_credentials(conjur_url)

    def get_store_location(self):
        return "SimpleCredentialsProvider"
