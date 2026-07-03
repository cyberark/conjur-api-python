import asyncio
import base64
import hashlib
import json
import secrets
import ssl
import time
from urllib.parse import urlparse, parse_qs, urlencode
from urllib.request import Request, urlopen, HTTPRedirectHandler, HTTPSHandler, build_opener

import pytest
from aiounittest import AsyncTestCase

from conjur_api.errors.errors import HttpStatusError
from conjur_api.models.general.credentials_data import OidcCodeDetail
from tests.integration.integ_utils import (AuthenticationStrategyType,
                                           create_admin_client,
                                           create_client)

OIDC_SERVER_URL = 'https://oidc-server'
OIDC_USERNAME = 'john.williams'
OIDC_SERVICE_ID = 'test-service'
REDIRECT_URI = 'http://conjur-https/authn-oidc/test-service/callback'

# The mock OIDC server presents a self-signed certificate generated at
# container startup and shared via the oidc-certs volume (see
# docker-compose.yml and ci/test/test_integration). Trust that exact
# certificate rather than disabling verification.
_OIDC_CERT_PATH = '/oidc-certs/oidc-server.cert.pem'


def _oidc_ssl_context() -> ssl.SSLContext:
    for _ in range(30):
        try:
            return ssl.create_default_context(cafile=_OIDC_CERT_PATH)
        except FileNotFoundError:
            time.sleep(1)
    return ssl.create_default_context(cafile=_OIDC_CERT_PATH)


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def _mock_server_config() -> dict:
    with urlopen(f'{OIDC_SERVER_URL}/mock/config', context=_oidc_ssl_context()) as response:
        return json.loads(response.read())


def _queue_mock_user(subject: str) -> None:
    body = json.dumps({'subject': subject}).encode()
    request = Request(f'{OIDC_SERVER_URL}/mock/queue-user', data=body, method='POST')
    request.add_header('Content-Type', 'application/json')
    urlopen(request, context=_oidc_ssl_context())


def _get_authorization_code(client_id: str, nonce: str, code_verifier: str) -> str:
    """Drive the mock OIDC server's authorize endpoint, which redirects with a
    code immediately (no login form), and return the issued code."""
    digest = hashlib.sha256(code_verifier.encode()).digest()
    code_challenge = base64.urlsafe_b64encode(digest).rstrip(b'=').decode()

    params = {
        'response_type': 'code',
        'client_id': client_id,
        'redirect_uri': REDIRECT_URI,
        'scope': 'openid profile',
        'state': secrets.token_urlsafe(8),
        'nonce': nonce,
        'code_challenge': code_challenge,
        'code_challenge_method': 'S256',
    }
    url = f'{OIDC_SERVER_URL}/oidc/authorize?{urlencode(params)}'

    opener = build_opener(_NoRedirect, HTTPSHandler(context=_oidc_ssl_context()))
    try:
        opener.open(url)
        assert False, "Expected a 302 redirect from the mock OIDC server"
    except Exception as exc:
        location = exc.headers.get('Location', '') if hasattr(exc, 'headers') else ''
        assert location, f"Expected redirect Location header, got: {exc}"

    parsed = urlparse(location)
    params = parse_qs(parsed.query)
    assert 'code' in params, f"No 'code' in redirect location: {location}"
    return params['code'][0]


@pytest.mark.integration
class TestOidcAuthentication(AsyncTestCase):

    @classmethod
    def setUpClass(cls):
        asyncio.run(cls._add_test_data())

    @classmethod
    async def _add_test_data(cls):
        config = _mock_server_config()
        cls.client_id = config['client_id']

        c = await create_admin_client()
        await c.set('conjur/authn-oidc/test-service/provider-uri', f'{OIDC_SERVER_URL}/oidc')
        await c.set('conjur/authn-oidc/test-service/client-id', config['client_id'])
        await c.set('conjur/authn-oidc/test-service/client-secret', config['client_secret'])
        await c.set('conjur/authn-oidc/test-service/claim-mapping', 'sub')
        await c.set('conjur/authn-oidc/test-service/redirect-uri', REDIRECT_URI)

        providers = await c.list_oidc_providers()
        provider = next((p for p in providers if p.get('service_id') == OIDC_SERVICE_ID), None)
        assert provider is not None, f"Expected service_id '{OIDC_SERVICE_ID}' in providers, got: {providers}"

        cls.nonce = provider['nonce']
        cls.code_verifier = provider['code_verifier']

    async def test_oidc_authentication_success(self):
        _queue_mock_user(OIDC_USERNAME)
        code = _get_authorization_code(self.client_id, self.nonce, self.code_verifier)
        detail = OidcCodeDetail(code=code, code_verifier=self.code_verifier, nonce=self.nonce)

        c = await create_client(None, None, AuthenticationStrategyType.OIDC,
                                service_id=OIDC_SERVICE_ID, oidc_code_detail=detail)

        response = await c.whoami()
        self.assertEqual(response['username'], OIDC_USERNAME)

    async def test_oidc_authentication_failure_invalid_code(self):
        detail = OidcCodeDetail(code='invalid-code', code_verifier=self.code_verifier, nonce=self.nonce)

        c = await create_client(None, None, AuthenticationStrategyType.OIDC,
                                service_id=OIDC_SERVICE_ID, oidc_code_detail=detail)

        with self.assertRaises(HttpStatusError) as context:
            await c.whoami()
        self.assertEqual(context.exception.status, 400)
