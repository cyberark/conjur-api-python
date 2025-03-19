import asyncio
import ssl
import unittest

from enum import Enum
from unittest.mock import patch, call

from aiounittest import AsyncTestCase
from aiohttp import ClientSSLError
from aiohttp.client_reqrep import ConnectionKey
from asynctest import patch

from aiohttp import BasicAuth

from conjur_api.models import SslVerificationMode, SslVerificationMetadata, ProxyParams
from conjur_api.errors.errors import HttpSslError
from conjur_api.wrappers.http_wrapper import HttpVerb, invoke_endpoint
from tests.https.common import MockResponse


class HttpVerbTest(unittest.TestCase):
    def test_http_verb_has_all_the_verbs_expected(self):
        self.assertTrue(HttpVerb.GET)
        self.assertTrue(HttpVerb.PUT)
        self.assertTrue(HttpVerb.POST)
        self.assertTrue(HttpVerb.DELETE)
        self.assertTrue(HttpVerb.PATCH)
        self.assertTrue(HttpVerb.HEAD)


def create_ssl_verification_metadata(mode=SslVerificationMode.TRUST_STORE, cert_path=None):
    return SslVerificationMetadata(mode, cert_path)


class HttpInvokeEndpointTest(AsyncTestCase):
    UNESCAPED_PARAMS = {
        'url': 'https://foo.bar',
        'one': 'abc/$!@#$%^&*() \\[]{}',
        'two': ')(*&^%$#@![]{} <>?',
    }

    ESCAPED_PARAMS = [
        'abc%2F%24%21%40%23%24%25%5E%26%2A%28%29%20%5C%5B%5D%7B%7D',
        '%29%28%2A%26%5E%25%24%23%40%21%5B%5D%7B%7D%20%3C%3E%3F',
    ]

    class MockEndpoint(Enum):
        NO_PARAMS = "no/params"
        WITH_URL = "{url}/no/params"
        PARAMETER_ESCAPING = "{url}/{one}/{two}"

    @patch('aiohttp.ClientSession.request')
    async def test_invoke_endpoint_can_invoke_http_client(self, mock_request):
        ssl_context = ssl.create_default_context()
        with patch.object(ssl, 'create_default_context', return_value=ssl_context) as mock_create_ssl_context:
            mock_request.return_value = MockResponse('', 200)
            await invoke_endpoint(HttpVerb.GET, self.MockEndpoint.NO_PARAMS, {})

            mock_create_ssl_context.assert_called_once_with()
            mock_request.assert_called_once_with('GET', 'no/params', auth=None, headers={'x-cybr-telemetry': 'aW49U2VjcmV0c01hbmFnZXJQeXRob24gU0RLJml0PWN5YnItc2VjcmV0c21hbmFnZXImaXY9Tm8gVmVyc2lvbiBGb3VuZCZ2bj1DeWJlckFyaw'}, data='', ssl=ssl_context,
                                                 params=None, proxy=None)

    @patch('aiohttp.ClientSession.request')
    async def test_invoke_endpoint_can_handle_unset_params(self, mock_request):
        ssl_context = ssl.create_default_context()
        with patch.object(ssl, 'create_default_context', return_value=ssl_context) as mock_create_ssl_context:
            mock_request.return_value = MockResponse('', 200)
            await invoke_endpoint(HttpVerb.GET, self.MockEndpoint.NO_PARAMS, None)

            mock_create_ssl_context.assert_called_once_with()
            mock_request.assert_called_once_with('GET', 'no/params', auth=None, headers={'x-cybr-telemetry': 'aW49U2VjcmV0c01hbmFnZXJQeXRob24gU0RLJml0PWN5YnItc2VjcmV0c21hbmFnZXImaXY9Tm8gVmVyc2lvbiBGb3VuZCZ2bj1DeWJlckFyaw'}, data='', ssl=ssl_context,
                                                 params=None, proxy=None)
    
    @patch('aiohttp.ClientSession.request')
    async def test_invoke_endpoint_uses_http_verb_for_method_name(self, mock_request):
        ssl_context = ssl.create_default_context()
        with patch.object(ssl, 'create_default_context', return_value=ssl_context) as mock_create_ssl_context:
            mock_request.return_value = MockResponse('', 200)
            await invoke_endpoint(HttpVerb.GET, self.MockEndpoint.NO_PARAMS, {})
            mock_create_ssl_context.assert_called_with()
            mock_request.assert_called_with('GET', 'no/params', auth=None, headers={'x-cybr-telemetry': 'aW49U2VjcmV0c01hbmFnZXJQeXRob24gU0RLJml0PWN5YnItc2VjcmV0c21hbmFnZXImaXY9Tm8gVmVyc2lvbiBGb3VuZCZ2bj1DeWJlckFyaw'}, data='', ssl=ssl_context,
                                            params=None, proxy=None)

            await invoke_endpoint(HttpVerb.POST, self.MockEndpoint.NO_PARAMS, {})
            mock_request.assert_called_with('POST', 'no/params', auth=None, headers={'x-cybr-telemetry': 'aW49U2VjcmV0c01hbmFnZXJQeXRob24gU0RLJml0PWN5YnItc2VjcmV0c21hbmFnZXImaXY9Tm8gVmVyc2lvbiBGb3VuZCZ2bj1DeWJlckFyaw'}, data='', ssl=ssl_context,
                                            params=None, proxy=None)

            await invoke_endpoint(HttpVerb.DELETE, self.MockEndpoint.NO_PARAMS, {})
            mock_request.assert_called_with('DELETE', 'no/params', auth=None, headers={'x-cybr-telemetry': 'aW49U2VjcmV0c01hbmFnZXJQeXRob24gU0RLJml0PWN5YnItc2VjcmV0c21hbmFnZXImaXY9Tm8gVmVyc2lvbiBGb3VuZCZ2bj1DeWJlckFyaw'}, data='', ssl=ssl_context,
                                            params=None, proxy=None)
    
    @patch('aiohttp.ClientSession.request')
    async def test_invoke_endpoint_generates_url_from_endpoint_object(self, mock_request):
        ssl_context = ssl.create_default_context()
        with patch.object(ssl, 'create_default_context', return_value=ssl_context) as mock_create_ssl_context:
            mock_request.return_value = MockResponse('', 200)
            await invoke_endpoint(HttpVerb.GET, self.MockEndpoint.WITH_URL, {'url': 'http://host'})

            mock_create_ssl_context.assert_called_once_with()
            mock_request.assert_called_once_with('GET', 'http://host/no/params', auth=None, headers={'x-cybr-telemetry': 'aW49U2VjcmV0c01hbmFnZXJQeXRob24gU0RLJml0PWN5YnItc2VjcmV0c21hbmFnZXImaXY9Tm8gVmVyc2lvbiBGb3VuZCZ2bj1DeWJlckFyaw'}, data='',
                                                 ssl=ssl_context, params=None, proxy=None)
    
    @patch('aiohttp.ClientSession.request')
    async def test_invoke_endpoint_attaches_api_token_header_if_present_in_params(self, mock_request):
        ssl_context = ssl.create_default_context()
        with patch.object(ssl, 'create_default_context', return_value=ssl_context) as mock_create_ssl_context:
            mock_request.return_value = MockResponse('', 200)
            await invoke_endpoint(HttpVerb.GET, self.MockEndpoint.NO_PARAMS, None, api_token='token')

            mock_create_ssl_context.assert_called_once_with()
            mock_request.assert_called_once_with('GET', 'no/params', auth=None, data='', ssl=ssl_context,
                                                 headers={'x-cybr-telemetry': 'aW49U2VjcmV0c01hbmFnZXJQeXRob24gU0RLJml0PWN5YnItc2VjcmV0c21hbmFnZXImaXY9Tm8gVmVyc2lvbiBGb3VuZCZ2bj1DeWJlckFyaw','Authorization': 'Token token="dG9rZW4="'}, params=None,
                                                 proxy=None)
    
    @patch('aiohttp.ClientSession.request')
    async def test_invoke_endpoint_verifies_ssl_by_default(self, mock_request):
        ssl_context = ssl.create_default_context()
        with patch.object(ssl, 'create_default_context', return_value=ssl_context) as mock_create_ssl_context:
            mock_request.return_value = MockResponse('', 200)
            await invoke_endpoint(HttpVerb.GET, self.MockEndpoint.NO_PARAMS, None)

            mock_create_ssl_context.assert_called_once_with()
            mock_request.assert_called_once_with('GET', 'no/params', auth=None, data='', ssl=ssl_context, headers={'x-cybr-telemetry': 'aW49U2VjcmV0c01hbmFnZXJQeXRob24gU0RLJml0PWN5YnItc2VjcmV0c21hbmFnZXImaXY9Tm8gVmVyc2lvbiBGb3VuZCZ2bj1DeWJlckFyaw'},
                                                 params=None, proxy=None)
    
    @patch('aiohttp.ClientSession.request')
    async def test_invoke_endpoint_ssl_verify_param_defaults_to_true_to_http_client(self, mock_request):
        ssl_context = ssl.create_default_context()
        with patch.object(ssl, 'create_default_context', return_value=ssl_context) as mock_create_ssl_context:
            mock_request.return_value = MockResponse('', 200)
            await invoke_endpoint(HttpVerb.GET, self.MockEndpoint.NO_PARAMS, None,
                                        ssl_verification_metadata=create_ssl_verification_metadata())

            mock_create_ssl_context.assert_called_once_with()
            mock_request.assert_called_once_with('GET', 'no/params', auth=None, data='', ssl=ssl_context, headers={'x-cybr-telemetry': 'aW49U2VjcmV0c01hbmFnZXJQeXRob24gU0RLJml0PWN5YnItc2VjcmV0c21hbmFnZXImaXY9Tm8gVmVyc2lvbiBGb3VuZCZ2bj1DeWJlckFyaw'},
                                                 params=None, proxy=None)
    
    @patch('aiohttp.ClientSession.request')
    async def test_invoke_endpoint_raises_hostname_mismatch_error(self, mock_request):
        mock_request.side_effect = ClientSSLError(ConnectionKey(None, None, None, None, None, None, None),
                                                  OSError())
        ssl_context = ssl.create_default_context()
        with patch.object(ssl, 'create_default_context', return_value=ssl_context) as mock_create_ssl_context:
            with self.assertRaises(HttpSslError):
                await invoke_endpoint(HttpVerb.GET, self.MockEndpoint.NO_PARAMS, None,
                                            ssl_verification_metadata=create_ssl_verification_metadata(
                                                SslVerificationMode.SELF_SIGN, 'foo'),
                                            check_errors=False)

            ssl_context_calls = [call(cafile='foo')]
            mock_create_ssl_context.assert_has_calls(ssl_context_calls)
            mock_request.assert_called_with('GET', 'no/params', auth=None, data='', ssl=ssl_context, headers={'x-cybr-telemetry': 'aW49U2VjcmV0c01hbmFnZXJQeXRob24gU0RLJml0PWN5YnItc2VjcmV0c21hbmFnZXImaXY9Tm8gVmVyc2lvbiBGb3VuZCZ2bj1DeWJlckFyaw'},
                                            params=None, proxy=None)
    
    @patch('aiohttp.ClientSession.request')
    async def test_invoke_endpoint_passes_auth_param_to_http_client_if_provided(self, mock_request):
        ssl_context = ssl.create_default_context()
        with patch.object(ssl, 'create_default_context', return_value=ssl_context) as mock_create_ssl_context:
            mock_request.return_value = MockResponse('', 200)
            await invoke_endpoint(HttpVerb.GET, self.MockEndpoint.NO_PARAMS, None, auth=('foo', 'bar'))

            mock_create_ssl_context.assert_called_once_with()
            mock_request.assert_called_once_with('GET', 'no/params', auth=BasicAuth('foo', 'bar'), data='',
                                                 ssl=ssl_context, headers={'x-cybr-telemetry': 'aW49U2VjcmV0c01hbmFnZXJQeXRob24gU0RLJml0PWN5YnItc2VjcmV0c21hbmFnZXImaXY9Tm8gVmVyc2lvbiBGb3VuZCZ2bj1DeWJlckFyaw'}, params=None, proxy=None)
    
    @patch('aiohttp.ClientSession.request')
    async def test_invoke_endpoint_passes_extra_args_to_http_client(self, mock_request):
        ssl_context = ssl.create_default_context()
        with patch.object(ssl, 'create_default_context', return_value=ssl_context) as mock_create_ssl_context:
            mock_request.return_value = MockResponse('', 200)
            await invoke_endpoint(HttpVerb.GET, self.MockEndpoint.NO_PARAMS, None, 'ab')

            mock_create_ssl_context.assert_called_once_with()
            mock_request.assert_called_once_with('GET', 'no/params', auth=None, data='ab', ssl=ssl_context,
                                                 headers={'x-cybr-telemetry': 'aW49U2VjcmV0c01hbmFnZXJQeXRob24gU0RLJml0PWN5YnItc2VjcmV0c21hbmFnZXImaXY9Tm8gVmVyc2lvbiBGb3VuZCZ2bj1DeWJlckFyaw'}, params=None, proxy=None)
    
    @patch('aiohttp.ClientSession.request')
    async def test_invoke_endpoint_passes_query_param(self, mock_request):
        ssl_context = ssl.create_default_context()
        with patch.object(ssl, 'create_default_context', return_value=ssl_context) as mock_create_ssl_context:
            query = {
                'foo!@#$': 'a',
                'bar)(*&^%': 'b',
            }
            mock_request.return_value = MockResponse('', 200)
            await invoke_endpoint(HttpVerb.GET, self.MockEndpoint.NO_PARAMS, None, 'ab', query=query)

            mock_create_ssl_context.assert_called_once_with()
            mock_request.assert_called_once_with('GET', 'no/params', auth=None, data='ab', ssl=ssl_context,
                                                 headers={'x-cybr-telemetry': 'aW49U2VjcmV0c01hbmFnZXJQeXRob24gU0RLJml0PWN5YnItc2VjcmV0c21hbmFnZXImaXY9Tm8gVmVyc2lvbiBGb3VuZCZ2bj1DeWJlckFyaw'}, params=query, proxy=None)
    
    @patch('aiohttp.ClientSession.request')
    async def test_invoke_endpoint_passes_proxy_param(self, mock_request):
        ssl_context = ssl.create_default_context()
        with patch.object(ssl, 'create_default_context', return_value=ssl_context) as mock_create_ssl_context:
            mock_request.return_value = MockResponse('', 200)
            await invoke_endpoint(HttpVerb.GET, self.MockEndpoint.NO_PARAMS, None, 'ab',
                                  proxy_params=ProxyParams('proxy.com'))

            mock_create_ssl_context.assert_called_once_with()
            mock_request.assert_called_once_with('GET', 'no/params', auth=None, data='ab', ssl=ssl_context,
                                                 headers={'x-cybr-telemetry': 'aW49U2VjcmV0c01hbmFnZXJQeXRob24gU0RLJml0PWN5YnItc2VjcmV0c21hbmFnZXImaXY9Tm8gVmVyc2lvbiBGb3VuZCZ2bj1DeWJlckFyaw'}, params=None, proxy='proxy.com')
    
    @patch('aiohttp.ClientSession.request')
    async def test_invoke_endpoint_quotes_all_params_except_url(self, mock_request):
        ssl_context = ssl.create_default_context()
        with patch.object(ssl, 'create_default_context', return_value=ssl_context) as mock_create_ssl_context:
            mock_request.return_value = MockResponse('', 200)
            await invoke_endpoint(HttpVerb.GET, self.MockEndpoint.PARAMETER_ESCAPING,
                                        self.UNESCAPED_PARAMS, '$#\\% ^%')

            quoted_endpoint = '/'.join([self.UNESCAPED_PARAMS['url']] + self.ESCAPED_PARAMS)
            mock_create_ssl_context.assert_called_once_with()
            mock_request.assert_called_once_with('GET', quoted_endpoint, data='$#\\% ^%', auth=None,
                                                 ssl=ssl_context, headers={'x-cybr-telemetry': 'aW49U2VjcmV0c01hbmFnZXJQeXRob24gU0RLJml0PWN5YnItc2VjcmV0c21hbmFnZXImaXY9Tm8gVmVyc2lvbiBGb3VuZCZ2bj1DeWJlckFyaw'}, params=None, proxy=None)

    @patch('aiohttp.ClientSession.request')
    async def test_invoke_endpoint_raises_error_if_bad_status_code_is_returned(self, mock_request):
        class MockResponse(object):
            def raise_for_status(self):
                raise Exception('bad status code!')

        mock_request.return_value = MockResponse()

        with self.assertRaises(Exception) as context:
            await invoke_endpoint(HttpVerb.GET, self.MockEndpoint.NO_PARAMS, None)

    @patch('aiohttp.ClientSession.request')
    async def test_invoke_endpoint_does_not_raise_error_if_bad_status_but_check_errors_is_false(self, mock_request):
        mock_request.return_value = MockResponse('', 400)

        await invoke_endpoint(HttpVerb.GET, self.MockEndpoint.NO_PARAMS, None, check_errors=False)

    @patch('aiohttp.ClientSession.request')
    async def test_invoke_endpoint_returns_http_client_response(self, mock_request):
        mock_request.return_value = MockResponse('{"a": 123}', 200)

        response = await invoke_endpoint(HttpVerb.GET, self.MockEndpoint.NO_PARAMS, None)

        self.assertEqual(response.json, {'a': 123})
