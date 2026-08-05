import asyncio
import os

import pytest
from aiounittest import AsyncTestCase

from conjur_api import Client
from conjur_api.models import SslVerificationMode
from conjur_api.models.general.conjur_connection_info import ConjurConnectionInfo
from conjur_api.providers.cert_authentication_strategy import CertAuthenticationStrategy
from tests.integration.integ_utils import create_admin_client, _conjur_url


def _cert_env_vars_present() -> bool:
    return all(os.getenv(v) for v in [
        'CONJUR_AUTHN_CERT_FILE',
        'CONJUR_AUTHN_CERT_KEY_FILE',
        'CONJUR_AUTHN_CERT_SERVICE_ID',
    ])


def _create_cert_client(host_id: str = None) -> Client:
    conjur_url = _conjur_url()
    service_id = os.environ['CONJUR_AUTHN_CERT_SERVICE_ID']
    cert_file = os.environ['CONJUR_AUTHN_CERT_FILE']
    key_file = os.environ['CONJUR_AUTHN_CERT_KEY_FILE']

    connection_info = ConjurConnectionInfo(
        conjur_url=conjur_url,
        account="conjur",
        service_id=service_id,
    )
    authn_strategy = CertAuthenticationStrategy(
        cert_file=cert_file,
        key_file=key_file,
        service_id=service_id,
        host_id=host_id,
    )
    return Client(connection_info, authn_strategy=authn_strategy,
                  ssl_verification_mode=SslVerificationMode.INSECURE, debug=True)


@pytest.mark.integration
@pytest.mark.skipif(not _cert_env_vars_present(),
                    reason="CONJUR_AUTHN_CERT_FILE / CONJUR_AUTHN_CERT_KEY_FILE / CONJUR_AUTHN_CERT_SERVICE_ID not set")
class TestCertAuthentication(AsyncTestCase):

    @classmethod
    def setUpClass(cls):
        asyncio.run(cls._add_test_data())

    @classmethod
    async def _add_test_data(cls):
        admin = await create_admin_client()
        await admin.load_policy_file("conjur/authn-cert", "tests/integration/policies/authn-cert.yml")
        await admin.set_authenticator_state(
            f"authn-cert/{os.environ['CONJUR_AUTHN_CERT_SERVICE_ID']}", True
        )

    async def test_cert_authentication_request_mode(self):
        host_id = os.environ.get('CONJUR_AUTHN_CERT_HOST_ID')
        if not host_id:
            self.skipTest("CONJUR_AUTHN_CERT_HOST_ID not set — skipping request-mode test")

        client = _create_cert_client(host_id=host_id)
        response = await client.whoami()
        self.assertIn('username', response)

    async def test_cert_authentication_spiffe_mode(self):
        if not os.getenv('TEST_CERT_SPIFFE'):
            self.skipTest("TEST_CERT_SPIFFE not set — skipping SPIFFE-mode test")

        client = _create_cert_client(host_id=None)
        response = await client.whoami()
        self.assertIn('username', response)
