import io
import logging

from aiounittest import AsyncTestCase

from conjur_api.http.ssl import ssl_context_factory
from conjur_api.models import SslVerificationMetadata, SslVerificationMode


class SslContextFactoryTest(AsyncTestCase):
    async def test_create_ssl_context_with_trust_store(self):
        # Redirect logging to a buffer
        log_stream = io.StringIO()
        log_output = logging.StreamHandler(log_stream)
        logging.getLogger().addHandler(log_output)
        original_level = logging.getLogger().level
        logging.getLogger().setLevel(logging.DEBUG)

        # Create SSLContext with TrustStore
        ssl_verification_metadata = SslVerificationMetadata(SslVerificationMode.TRUST_STORE)
        ssl_context = ssl_context_factory.create_ssl_context(ssl_verification_metadata)
        self.assertIsNotNone(ssl_context)

        # Remove the handler
        logging.getLogger().removeHandler(log_output)
        logging.getLogger().setLevel(original_level)

        # Verify the log output
        log_stream.seek(0)
        self.assertIn("Creating SSLContext from OS TrustStore for 'LINUX'", log_stream.read())
