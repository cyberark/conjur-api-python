import asyncio
from enum import Enum

from aiounittest import AsyncTestCase

from conjur_api.models import SslVerificationMetadata, SslVerificationMode
from conjur_api.errors.errors import HttpSslError, CertificateHostnameMismatchException
from conjur_api.wrappers.http_wrapper import HttpVerb, invoke_endpoint


invalid_badssl_endpoints = [
    "https://expired.badssl.com",
    "https://incomplete-chain.badssl.com",
    # "https://invalid-expected-sct.badssl.com",
    # "https://known-interception.badssl.com",
    "https://no-common-name.badssl.com",
    # "https://no-sct.badssl.com",
    "https://no-subject.badssl.com",
    # "https://pinning-test.badssl.com",  # Currently supported but shouldn't.
    "https://reversed-chain.badssl.com",
    # "https://revoked.badssl.com",  # Currently supported but shouldn't.
    "https://self-signed.badssl.com",
    "https://untrusted-root.badssl.com",
    "https://wrong.host.badssl.com",
    # "https://dh-composite.badssl.com",# Currently supported but shouldn't.
    # "https://dh1024.badssl.com", # Currently supported but shouldn't.
    "https://dh480.badssl.com",
    "https://dh512.badssl.com",
    # "https://static-rsa.badssl.com",  # Currently supported but shouldn't.
    # "https://ssl-v2.badssl.com",
    # "https://ssl-v3.badssl.com",
    # "https://tls-v1-0.badssl.com",
    # "https://tls-v1-1.badssl.com",
    "https://3des.badssl.com",
    "https://null.badssl.com",
    "https://rc4-md5.badssl.com",
    "https://rc4.badssl.com"
]

valid_badssl_endpoints = [
    "https://ecc256.badssl.com",
    "https://ecc384.badssl.com",
    # This is temporarily broken, see https://github.com/chromium/badssl.com/issues/511
    # "https://extended-validation.badssl.com",
    "https://rsa2048.badssl.com",
    "https://rsa4096.badssl.com",
    # This is temporarily broken, see https://github.com/chromium/badssl.com/issues/501
    # "https://rsa8192.badssl.com",
    "https://sha256.badssl.com",
    # These are temporarily broken, see https://github.com/chromium/badssl.com/issues/501
    # "https://sha384.badssl.com",
    # "https://sha512.badssl.com",
    "https://tls-v1-2.badssl.com",
    "https://cbc.badssl.com"
]


class TestDemonstrateSubtest(AsyncTestCase):
    class MockEndpoint(Enum):
        BADSSL_URL = "{url}"

    async def test_http_wrapper_get_invalid_badssl_endpoints_throws_ssl_exception(self):
        for badssl_url in invalid_badssl_endpoints:
            with self.subTest(msg=f"Validate SSL cert of '{badssl_url}' is not valid"):
                expected_exceptions = (HttpSslError, CertificateHostnameMismatchException)
                with self.assertRaises(expected_exceptions):
                    await invoke_endpoint(HttpVerb.GET,
                                                endpoint=self.MockEndpoint.BADSSL_URL,
                                                params={'url': badssl_url},
                                                ssl_verification_metadata=SslVerificationMetadata(
                                                    SslVerificationMode.TRUST_STORE),
                                                check_errors=False)

    async def test_http_wrapper_get_valid_badssl_endpoints_successfully(self):
        for badssl_url in valid_badssl_endpoints:
            with self.subTest(msg=f"Validate SSL cert of '{badssl_url}' is valid"):
                await invoke_endpoint(HttpVerb.GET,
                                            endpoint=self.MockEndpoint.BADSSL_URL,
                                            params={'url': badssl_url},
                                            ssl_verification_metadata=SslVerificationMetadata(
                                                SslVerificationMode.TRUST_STORE),
                                            check_errors=False)
