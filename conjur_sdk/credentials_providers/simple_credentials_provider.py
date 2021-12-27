from typing import Dict

from conjur_sdk.interface import CredentialsProviderInterface
from conjur_sdk.models import CredentialsData


class SimpleCredentialsProvider(CredentialsProviderInterface):

    def __init__(self):
        self.credentials: Dict[str, CredentialsData] = {}

    def save(self, credential_data: CredentialsData):
        self.credentials[credential_data.machine] = credential_data

    def load(self, conjurrc_conjur_url: str) -> CredentialsData:
        return self.credentials[conjurrc_conjur_url]

    def update_api_key_entry(self, user_to_update: str, credential_data: CredentialsData, new_api_key: str):
        pass

    def remove_credentials(self, conjur_url: str):
        del self.credentials[conjur_url]

    def is_exists(self, conjurrc_conjur_url: str) -> bool:
        return self.credentials[conjurrc_conjur_url] is not None

    def cleanup_if_exists(self, conjur_url: str):
        if self.is_exists(conjur_url):
            self.remove_credentials(conjur_url)

    def get_store_location(self):
        return "SimpleCredentialsProvider"
