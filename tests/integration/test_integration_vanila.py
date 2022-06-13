import datetime
import os

from aiounittest import AsyncTestCase

from conjur_api import Client
from conjur_api.models import  SslVerificationMode, ConjurConnectionInfo, CredentialsData
from conjur_api.providers import AuthnAuthenticationStrategy, LdapAuthenticationStrategy, SimpleCredentialsProvider


class TestIntegrationVanila(AsyncTestCase):

    async def test_integration_vanilla(self):
        """
        This is a dummy test making sure integration tests jenkins step works.
        Once integration tests will be added this test should be removed
        @return:
        """
        conjur_url = "https://conjur-https"
        username = "admin"
        account = "dev"
        api_key = os.environ['CONJUR_AUTHN_API_KEY']
        conjur_data = ConjurConnectionInfo(
            conjur_url=conjur_url,
            account=account
        )
        credentials_provider = SimpleCredentialsProvider()
        authn_provider = AuthnAuthenticationStrategy(credentials_provider)
        credentials = CredentialsData(username=username, api_key=api_key, machine=conjur_url)
        credentials_provider.save(credentials)
        c = Client(conjur_data, authn_strategy=authn_provider,
                   ssl_verification_mode=SslVerificationMode.INSECURE)
        resources = await c.list()
        self.assertEqual(len(resources), 6)

    async def test_integration_vanilla_ldap(self):
        """
        This is a simple happy path test making sure authn-ldap works.
        @return:
        """
        conjur_url = "https://conjur-https"
        username = "alice"
        password = "alice"
        account = "dev"
        ldap_service_id = "test-service"
        conjur_data = ConjurConnectionInfo(
            conjur_url=conjur_url,
            account=account,
            service_id=ldap_service_id
        )
        credentials_provider = SimpleCredentialsProvider()
        authn_provider = LdapAuthenticationStrategy(credentials_provider)
        credentials = CredentialsData(username=username, password=password, machine=conjur_url)
        credentials_provider.save(credentials)
        c = Client(conjur_data, authn_strategy=authn_provider,
                   ssl_verification_mode=SslVerificationMode.INSECURE)
        resources = await c.list()
        self.assertEqual(len(resources), 2)
