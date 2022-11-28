import datetime
import os
import ssl

from aiounittest import AsyncTestCase
from unittest.mock import patch

from conjur_api import Client
from conjur_api.models import  SslVerificationMode, SslVerificationMetadata, ConjurConnectionInfo, CredentialsData
from conjur_api.providers import AuthnAuthenticationStrategy, LdapAuthenticationStrategy, SimpleCredentialsProvider
from conjur_api.http.ssl import ssl_context_factory


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
        self.assertGreater(len(resources), 6)

    async def test_integration_vanilla_ldap(self):
        """
        This is a simple happy path test making sure authn-ldap works.
        @return:
        """
        conjur_url = "https://conjur-https"
        username = "alice"
        password = "alice"  # nosec
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

    @patch('ssl.SSLContext.load_verify_locations')
    async def test_integration_truststore(self, mock_load_verify_locations):
        """
        This is a simple happy path test making sure the SSL context with a
        CA pem file provided also contains system CA's
        """
        ssl_metadata = SslVerificationMetadata(
            SslVerificationMode.CA_BUNDLE,
            ca_cert_path='/some/path.pem'
            )
        ssl_context = ssl_context_factory.create_ssl_context(ssl_metadata)
        ssl_context_default = ssl.create_default_context()

        self.assertTrue(ssl_context.cert_store_stats().get('x509_ca') >= ssl_context_default.cert_store_stats().get('x509_ca'))
