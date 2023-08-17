from unittest import TestCase

from conjur_api.providers import SimpleCredentialsProvider
from conjur_api.models import CredentialsData, OidcCodeDetail


def create_credentials(machine: str = "machine", username: str = "some_username", password: str = "some_password", api_key: str = "some_api_key") -> CredentialsData:
    return CredentialsData(machine, username, password, api_key)

def oidc_v2_credential(machine: str="machine", code="code", code_verifier="coded_verifier", nonce="nonce") -> CredentialsData:
    oidc_detail = OidcCodeDetail(code, code_verifier, nonce)
    return CredentialsData(machine, oidc_detail)


class SimpleCredentialsProviderTest(TestCase):

    def test_vanilla_flow(self):
        provider = SimpleCredentialsProvider()
        credentials_data = create_credentials()
        provider.save(credentials_data)
        self.assertEqual(credentials_data, provider.load(credentials_data.machine))

    def test_with_two_credentials(self):
        provider = SimpleCredentialsProvider()

        credentials_data1 = create_credentials()
        provider.save(credentials_data1)

        credentials_data2 = create_credentials("machine2", "user2", "psswd2", "api_key2")
        provider.save(credentials_data2)

        self.assertEqual(credentials_data1, provider.load(credentials_data1.machine))
        self.assertEqual(credentials_data2, provider.load(credentials_data2.machine))

    def test_change_doesnt_effect_after_save(self):
        provider = SimpleCredentialsProvider()
        old_username = "old_username"

        credentials_data = create_credentials("some_machine", old_username)
        provider.save(credentials_data)
        credentials_data.username = "different_username"
        self.assertNotEqual(credentials_data, provider.load(credentials_data.machine))
        self.assertEqual(old_username, provider.load(credentials_data.machine).username)

    def test_update_credentials(self):
        credentials_data1 = create_credentials()
        provider = SimpleCredentialsProvider()
        provider.save(credentials_data1)

        credentials_data2 = create_credentials(username="different_user")
        provider = SimpleCredentialsProvider()
        provider.save(credentials_data2)
        self.assertEqual("different_user", provider.load(credentials_data1.machine).username)

    def test_credentials_are_exist(self):
        provider = SimpleCredentialsProvider()
        credentials_data = create_credentials()
        provider.save(credentials_data)
        self.assertTrue(provider.is_exists(credentials_data.machine))
        self.assertFalse(provider.is_exists("not_exists_machine"))

    def test_cleanup_credentials_if_exist(self):
        provider = SimpleCredentialsProvider()
        credentials_data = create_credentials()
        provider.save(credentials_data)
        provider.cleanup_if_exists(credentials_data.machine)

        self.assertFalse(provider.is_exists(credentials_data.machine))

    def test_cleanup_if_exists_doesnt_raise_if_not_exist(self):
        provider = SimpleCredentialsProvider()
        provider.cleanup_if_exists("not_exists_machine")

    def test_remove_credentials(self):
        provider = SimpleCredentialsProvider()
        credentials_data = create_credentials()
        provider.save(credentials_data)
        provider.remove_credentials(credentials_data.machine)
        self.assertFalse(provider.is_exists(credentials_data.machine))

    def test_get_store_location(self):
        provider = SimpleCredentialsProvider()
        self.assertEqual("SimpleCredentialsProvider",provider.get_store_location())

    def test_cleanup_oidc_v2_credentials_if_exist(self):
        provider = SimpleCredentialsProvider()
        credentials_data = oidc_v2_credential()
        provider.save(credentials_data)
        provider.cleanup_if_exists(credentials_data.machine)

        self.assertFalse(provider.is_exists(credentials_data.machine))

    def test_remove_oidc_v2_credentials(self):
        provider = SimpleCredentialsProvider()
        credentials_data = oidc_v2_credential()
        provider.save(credentials_data)
        provider.remove_credentials(credentials_data.machine)
        self.assertFalse(provider.is_exists(credentials_data.machine))