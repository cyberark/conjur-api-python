
from datetime import datetime, timedelta
from unittest import mock, IsolatedAsyncioTestCase
from unittest.mock import PropertyMock, mock_open, patch

from conjur_api.errors.errors import HttpError, HttpStatusError

from conjur_api.client import Client
from conjur_api.http.api import Api
from conjur_api.models import SslVerificationMode, CredentialsData
from conjur_api.models.general.conjur_connection_info import ConjurConnectionInfo
from conjur_api.models.general.proxy_params import ProxyParams
from conjur_api.models.general.resource import Resource
from conjur_api.models.hostfactory.create_host_data import CreateHostData
from conjur_api.models.hostfactory.create_token_data import CreateTokenData
from conjur_api.models.list.list_members_of_data import ListMembersOfData
from conjur_api.models.list.list_permitted_roles_data import ListPermittedRolesData
from conjur_api.models.ssl.ssl_verification_metadata import SslVerificationMetadata
from conjur_api.providers.authn_authentication_strategy import AuthnAuthenticationStrategy
from conjur_api.providers.oidc_authentication_strategy import OidcAuthenticationStrategy
from conjur_api.providers.simple_credentials_provider import SimpleCredentialsProvider
from conjur_api.wrappers.http_response import HttpResponse
from tests.https.test_unit_http import MockResponse


def exists_in_args(val, args):
    return any(val in str(t) for t in args)


class ClientTest(IsolatedAsyncioTestCase):

    def __init__(self, testname):
        super(ClientTest, self).__init__(testname)
        self.conjur_data = ConjurConnectionInfo(
            conjur_url='https://conjur-https',
            account='test',
            proxy_params=ProxyParams(proxy_url='proxy.com')
        )
        self.conjur_oidc_data = ConjurConnectionInfo(
            conjur_url='https://conjur-https',
            account='test',
            service_id='test-service',
            proxy_params=ProxyParams(proxy_url='proxy.com')
        )
        credential_provider = SimpleCredentialsProvider()
        credential_provider.save(CredentialsData(self.conjur_data.conjur_url, 'username', 'password', 'api_key'))
        self.authn_provider = AuthnAuthenticationStrategy(credential_provider)
        self.oidc_provider = OidcAuthenticationStrategy(credential_provider)

        self.ssl_verification_mode = SslVerificationMode.INSECURE
        self.ssl_verification_metadata = SslVerificationMetadata(self.ssl_verification_mode, None)

        self.client = Client(self.conjur_data, authn_strategy=self.authn_provider,
                             ssl_verification_mode=self.ssl_verification_mode)
        self.oidc_client = Client(self.conjur_oidc_data, authn_strategy=self.oidc_provider,
                                  ssl_verification_mode=self.ssl_verification_mode)

        # Shift the API token expiration ahead to avoid false negatives
        self.client._api.api_token_expiration = datetime.now() + timedelta(days=1)
        self.oidc_client._api.api_token_expiration = datetime.now() + timedelta(days=1)

    async def test_client_login_invokes_api(self):
        with mock.patch('conjur_api.providers.authn_authentication_strategy.AuthnAuthenticationStrategy.login') as mock_api_login:
            await self.client.login()
            mock_api_login.assert_called_once_with(self.conjur_data, self.ssl_verification_metadata)

    async def test_client_create_token_empty_value_raises_exception(self):
        with self.assertRaises(Exception) as context:
          await self.client.create_token(None)
          self.assertTrue('create_token_data is empty' in str(context.exception))

    @patch('conjur_api.http.api.invoke_endpoint')
    @patch.object(Api, '_api_token', new_callable=PropertyMock)
    async def test_client_create_token_invokes_api(self, mock_api_token, mock_invoke_endpoint):
      mock_api_token.return_value = 'test_token'
      create_token_data = CreateTokenData(host_factory='abcdefg', days=1)
      await self.client.create_token(create_token_data)

      args, kwargs = mock_invoke_endpoint.call_args
      self.assertEqual('test_token', kwargs.get('api_token'))
      self.assertEqual('proxy.com', kwargs.get('proxy_params').proxy_url)
      self.assertTrue(exists_in_args('abcdefg', args))
      mock_invoke_endpoint.assert_called_once()

    @patch('conjur_api.http.api.invoke_endpoint')
    @patch.object(Api, '_api_token', new_callable=PropertyMock)
    async def test_client_whoami_invokes_api(self, mock_api_token, mock_invoke_endpoint):
        mock_api_token.return_value = 'test_token'
        await self.client.whoami()

        args, kwargs = mock_invoke_endpoint.call_args
        self.assertEqual('test_token', kwargs.get('api_token'))
        self.assertEqual('proxy.com', kwargs.get('proxy_params').proxy_url)
        mock_invoke_endpoint.assert_called_once()

    @patch('conjur_api.http.api.invoke_endpoint')
    @patch.object(Api, '_api_token', new_callable=PropertyMock)
    async def test_client_revoke_token_invokes_api(self, mock_api_token, mock_invoke_endpoint):
        mock_api_token.return_value = 'test_token'
        await self.client.revoke_token('revoked_token')

        args, kwargs = mock_invoke_endpoint.call_args
        self.assertEqual('test_token', kwargs.get('api_token'))
        self.assertEqual('proxy.com', kwargs.get('proxy_params').proxy_url)
        self.assertTrue(exists_in_args('revoked_token', args))
        mock_invoke_endpoint.assert_called_once()

    @patch('conjur_api.http.api.invoke_endpoint')
    @patch.object(Api, '_api_token', new_callable=PropertyMock)
    async def test_client_list_permitted_roles_invokes_api(self, mock_api_token, mock_invoke_endpoint):
        mock_api_token.return_value = 'test_token'
        await self.client.list_permitted_roles(ListPermittedRolesData(kind='host', identifier='dummy-host', privilege='read'))

        args, kwargs = mock_invoke_endpoint.call_args
        self.assertEqual('test_token', kwargs.get('api_token'))
        self.assertEqual('proxy.com', kwargs.get('proxy_params').proxy_url)
        self.assertTrue(exists_in_args('dummy-host', args))
        mock_invoke_endpoint.assert_called_once()

    @patch('conjur_api.http.api.invoke_endpoint')
    @patch.object(Api, '_api_token', new_callable=PropertyMock)
    async def test_client_get_invokes_api(self, mock_api_token, mock_invoke_endpoint):
        mock_api_token.return_value = 'test_token'
        await self.client.get('dummy-var')

        args, kwargs = mock_invoke_endpoint.call_args
        self.assertEqual('test_token', kwargs.get('api_token'))
        self.assertEqual('proxy.com', kwargs.get('proxy_params').proxy_url)
        self.assertTrue(exists_in_args('dummy-var', args))
        mock_invoke_endpoint.assert_called_once()

    @patch('conjur_api.http.api.invoke_endpoint')
    async def test_client_create_host_invokes_api(self, mock_invoke_endpoint):
        await self.client.create_host(CreateHostData(host_id='abcdefg', token='test_token'))

        args, kwargs = mock_invoke_endpoint.call_args
        self.assertEqual('test_token', kwargs.get('api_token'))
        self.assertEqual('proxy.com', kwargs.get('proxy_params').proxy_url)
        self.assertTrue(exists_in_args('abcdefg', args))
        mock_invoke_endpoint.assert_called_once()

    @patch('conjur_api.http.api.invoke_endpoint')
    @patch.object(Api, '_api_token', new_callable=PropertyMock)
    async def test_client_set_invokes_api(self, mock_api_token, mock_invoke_endpoint):
        mock_api_token.return_value = 'test_token'
        await self.client.set('dummy-var', 'dummy-value')

        args, kwargs = mock_invoke_endpoint.call_args
        self.assertEqual('test_token', kwargs.get('api_token'))
        self.assertEqual('proxy.com', kwargs.get('proxy_params').proxy_url)
        self.assertTrue(exists_in_args('dummy-var', args) and exists_in_args('dummy-value', args))
        mock_invoke_endpoint.assert_called_once()

    @patch('conjur_api.http.api.invoke_endpoint')
    @patch.object(Api, '_api_token', new_callable=PropertyMock)
    async def test_client_load_policy_file_invokes_api(self, mock_api_token, mock_invoke_endpoint):
        mock_api_token.return_value = 'test_token'
        with patch('builtins.open', mock_open(read_data='!variable dummy-var')) as mock_file:
            await self.client.load_policy_file('test', 'my-policy.yml')

            args, kwargs = mock_invoke_endpoint.call_args
            self.assertEqual('test_token', kwargs.get('api_token'))
            self.assertEqual('proxy.com', kwargs.get('proxy_params').proxy_url)
            self.assertTrue(exists_in_args('test', args))
            mock_invoke_endpoint.assert_called_once()

    @patch('conjur_api.http.api.invoke_endpoint')
    @patch.object(Api, '_api_token', new_callable=PropertyMock)
    async def test_client_replace_policy_file_invokes_api(self, mock_api_token, mock_invoke_endpoint):
        mock_api_token.return_value = 'test_token'
        with patch('builtins.open', mock_open(read_data='!variable dummy-var')) as mock_file:
            await self.client.replace_policy_file('test', 'my-policy.yml')

            args, kwargs = mock_invoke_endpoint.call_args
            self.assertEqual('test_token', kwargs.get('api_token'))
            self.assertEqual('proxy.com', kwargs.get('proxy_params').proxy_url)
            self.assertTrue(exists_in_args('test', args))
            mock_invoke_endpoint.assert_called_once()

    @patch('conjur_api.http.api.invoke_endpoint')
    @patch.object(Api, '_api_token', new_callable=PropertyMock)
    async def test_client_update_policy_file_invokes_api(self, mock_api_token, mock_invoke_endpoint):
        mock_api_token.return_value = 'test_token'
        with patch('builtins.open', mock_open(read_data='!variable dummy-var')) as mock_file:
            await self.client.update_policy_file('test', 'my-policy.yml')

            args, kwargs = mock_invoke_endpoint.call_args
            self.assertEqual('test_token', kwargs.get('api_token'))
            self.assertEqual('proxy.com', kwargs.get('proxy_params').proxy_url)
            self.assertTrue(exists_in_args('test', args))
            mock_invoke_endpoint.assert_called_once()

    @patch('conjur_api.http.api.invoke_endpoint')
    @patch.object(Api, '_api_token', new_callable=PropertyMock)
    async def test_client_rotate_other_api_key_invokes_api(self, mock_api_token, mock_invoke_endpoint):
        mock_api_token.return_value = 'test_token'
        resource = Resource(kind='user', identifier='dummy-user')
        await self.client.rotate_other_api_key(resource)

        args, kwargs = mock_invoke_endpoint.call_args
        self.assertEqual('test_token', kwargs.get('api_token'))
        self.assertEqual('proxy.com', kwargs.get('proxy_params').proxy_url)
        self.assertIn('dummy-user', kwargs.get('query').get('role'))
        mock_invoke_endpoint.assert_called_once()

    @patch('conjur_api.http.api.invoke_endpoint')
    async def test_client_rotate_personal_api_key_invokes_api(self, mock_invoke_endpoint):
      await self.client.rotate_personal_api_key('dummy-user', 'dummy-password')

      args, kwargs = mock_invoke_endpoint.call_args
      self.assertTrue(exists_in_args('dummy-user', kwargs.get('auth')) and exists_in_args('dummy-password', kwargs.get('auth')))
      self.assertEqual('proxy.com', kwargs.get('proxy_params').proxy_url)
      mock_invoke_endpoint.assert_called_once()

    @patch('conjur_api.http.api.invoke_endpoint')
    async def test_client_get_server_info_invokes_api(self, mock_invoke_endpoint):
      await self.client.get_server_info()
      mock_invoke_endpoint.assert_called_once()
      args, kwargs = mock_invoke_endpoint.call_args
      self.assertEqual('proxy.com', kwargs.get('proxy_params').proxy_url)

    @patch('conjur_api.http.api.invoke_endpoint')
    async def test_client_change_personal_password_invokes_api(self, mock_invoke_endpoint):
        await self.client.change_personal_password('dummy-user', 'dummy-password', 'dummy-new-password')

        args, kwargs = mock_invoke_endpoint.call_args
        self.assertTrue(exists_in_args('dummy-user', kwargs.get('auth')) and exists_in_args('dummy-password', kwargs.get('auth')))
        self.assertTrue(exists_in_args('dummy-new-password', args))
        self.assertEqual('proxy.com', kwargs.get('proxy_params').proxy_url)
        mock_invoke_endpoint.assert_called_once()

    @patch('conjur_api.http.api.invoke_endpoint')
    @patch.object(Api, '_api_token', new_callable=PropertyMock)
    async def test_client_find_resource_by_identifier_invokes_api(self, mock_api_token, mock_invoke_endpoint):
        with self.assertRaises(Exception) as context:
            mock_api_token.return_value = 'test_token'
            json_data = '[{"id":"host:myHost"}]'
            mock_invoke_endpoint.return_value = HttpResponse(200, json_data, 'OK')
            await self.client.find_resource_by_identifier('host:myHost')

            args, kwargs = mock_invoke_endpoint.call_args
            self.assertEqual('test_token', kwargs.get('api_token'))
            self.assertEqual('proxy.com', kwargs.get('proxy_params').proxy_url)
            mock_invoke_endpoint.assert_called_once()
            self.assertTrue('Resource not found' in str(context.exception))

    @patch('conjur_api.http.api.invoke_endpoint')
    @patch.object(Api, '_api_token', new_callable=PropertyMock)
    async def test_client_find_resources_by_identifier_invokes_api(self, mock_api_token, mock_invoke_endpoint):
        mock_api_token.return_value = 'test_token'
        json_data = '[{"id":"host:myHost"}]'
        mock_invoke_endpoint.return_value = HttpResponse(200, json_data, 'OK')
        await self.client.find_resources_by_identifier('host:myHost')

        args, kwargs = mock_invoke_endpoint.call_args
        self.assertEqual('test_token', kwargs.get('api_token'))
        self.assertEqual('proxy.com', kwargs.get('proxy_params').proxy_url)
        self.assertIn('host:myHost', kwargs.get('query').get('search'))
        mock_invoke_endpoint.assert_called_once()

    @patch('conjur_api.http.api.invoke_endpoint')
    @patch.object(Api, '_api_token', new_callable=PropertyMock)
    async def test_client_list_members_of_role_invokes_api(self, mock_api_token, mock_invoke_endpoint):
        mock_api_token.return_value = 'test_token'
        resource = Resource(kind='variable', identifier='dummy-var')
        list_members_of_data = ListMembersOfData(kind='user', identifier='test')
        list_members_of_data.set_resource(resource)
        await self.client.list_members_of_role(list_members_of_data)

        args, kwargs = mock_invoke_endpoint.call_args
        self.assertEqual('test_token', kwargs.get('api_token'))
        self.assertEqual('proxy.com', kwargs.get('proxy_params').proxy_url)
        self.assertTrue(exists_in_args('dummy-var', args))
        mock_invoke_endpoint.assert_called_once()

    @patch('conjur_api.http.api.invoke_endpoint')
    @patch.object(Api, '_api_token', new_callable=PropertyMock)
    async def test_client_list_invokes_api(self, mock_api_token, mock_invoke_endpoint):
        mock_api_token.return_value = 'test_token'
        await self.client.list({'type': 'host'})

        args, kwargs = mock_invoke_endpoint.call_args
        self.assertEqual('test_token', kwargs.get('api_token'))
        self.assertEqual('proxy.com', kwargs.get('proxy_params').proxy_url)
        self.assertIn('host', kwargs.get('query').get('type'))
        mock_invoke_endpoint.assert_called_once()

    @patch('conjur_api.http.api.invoke_endpoint')
    @patch.object(Api, '_api_token', new_callable=PropertyMock)
    async def test_client_get_resource_invokes_api(self, mock_api_token, mock_invoke_endpoint):
        mock_api_token.return_value = 'test_token'
        await self.client.get_resource('policy', 'dummy')

        args, kwargs = mock_invoke_endpoint.call_args
        self.assertEqual('test_token', kwargs.get('api_token'))
        self.assertEqual('proxy.com', kwargs.get('proxy_params').proxy_url)
        self.assertTrue(exists_in_args('policy', args))
        self.assertTrue(exists_in_args('dummy', args))
        mock_invoke_endpoint.assert_called_once()

    @patch('conjur_api.http.api.invoke_endpoint')
    @patch.object(Api, '_api_token', new_callable=PropertyMock)
    async def test_client_resource_exists_invokes_api(self, mock_api_token, mock_invoke_endpoint):
        mock_api_token.return_value = 'test_token'
        await self.client.resource_exists('host', 'dummy')

        args, kwargs = mock_invoke_endpoint.call_args
        self.assertEqual('test_token', kwargs.get('api_token'))
        self.assertEqual('proxy.com', kwargs.get('proxy_params').proxy_url)
        self.assertTrue(exists_in_args('host', args))
        self.assertTrue(exists_in_args('dummy', args))
        mock_invoke_endpoint.assert_called_once()

    @patch('conjur_api.http.api.invoke_endpoint')
    @patch.object(Api, '_api_token', new_callable=PropertyMock)
    async def test_client_get_many_invokes_api(self, mock_api_token, mock_invoke_endpoint):
        mock_api_token.return_value = 'test_token'
        json_data = '{"test:variable:dummy-var":"myValue", \
                      "test:variable:dummy-var-2":"myValue-2",\
                      "test:variable:dummy-var-3":"myValue-3"}'
        mock_invoke_endpoint.return_value = HttpResponse(200, json_data, 'OK')
        await self.client.get_many('dummy-var', 'dummy-var-2', 'dummy-var-3')

        args, kwargs = mock_invoke_endpoint.call_args
        self.assertEqual('test_token', kwargs.get('api_token'))
        self.assertEqual('proxy.com', kwargs.get('proxy_params').proxy_url)
        self.assertIn('test:variable:dummy-var', kwargs.get('query').get('variable_ids'))
        self.assertIn('test:variable:dummy-var-2', kwargs.get('query').get('variable_ids'))
        self.assertIn('test:variable:dummy-var-3', kwargs.get('query').get('variable_ids'))
        mock_invoke_endpoint.assert_called_once()

    @patch('conjur_api.http.api.invoke_endpoint')
    @patch.object(Api, '_api_token', new_callable=PropertyMock)
    async def test_client_get_role_invokes_api(self, mock_api_token, mock_invoke_endpoint):
        mock_api_token.return_value = 'test_token'
        await self.client.get_role('policy', 'dummy')

        args, kwargs = mock_invoke_endpoint.call_args
        self.assertEqual('test_token', kwargs.get('api_token'))
        self.assertEqual('proxy.com', kwargs.get('proxy_params').proxy_url)
        self.assertTrue(exists_in_args('policy', args))
        self.assertTrue(exists_in_args('dummy', args))
        mock_invoke_endpoint.assert_called_once()

    @patch('conjur_api.http.api.invoke_endpoint')
    @patch.object(Api, '_api_token', new_callable=PropertyMock)
    async def test_client_role_exists_invokes_api(self, mock_api_token, mock_invoke_endpoint):
        mock_api_token.return_value = 'test_token'
        await self.client.role_exists('user', 'someuser')

        args, kwargs = mock_invoke_endpoint.call_args
        self.assertEqual('test_token', kwargs.get('api_token'))
        self.assertEqual('proxy.com', kwargs.get('proxy_params').proxy_url)
        self.assertTrue(exists_in_args('user', args))
        self.assertTrue(exists_in_args('someuser', args))
        mock_invoke_endpoint.assert_called_once()

    @patch('conjur_api.http.api.invoke_endpoint')
    @patch.object(Api, '_api_token', new_callable=PropertyMock)
    async def test_client_role_direct_memberships_invokes_api(self, mock_api_token, mock_invoke_endpoint):
        mock_api_token.return_value = 'test_token'
        await self.client.role_memberships('policy', 'dummy', True)

        args, kwargs = mock_invoke_endpoint.call_args
        self.assertEqual('test_token', kwargs.get('api_token'))
        self.assertEqual('proxy.com', kwargs.get('proxy_params').proxy_url)
        self.assertTrue(exists_in_args('policy', args))
        self.assertTrue(exists_in_args('dummy', args))
        self.assertTrue(exists_in_args('memberships', args))
        mock_invoke_endpoint.assert_called_once()

    @patch('conjur_api.http.api.invoke_endpoint')
    @patch.object(Api, '_api_token', new_callable=PropertyMock)
    async def test_client_role_memberships_invokes_api(self, mock_api_token, mock_invoke_endpoint):
        mock_api_token.return_value = 'test_token'
        await self.client.role_memberships('policy', 'dummy')

        args, kwargs = mock_invoke_endpoint.call_args
        self.assertEqual('test_token', kwargs.get('api_token'))
        self.assertEqual('proxy.com', kwargs.get('proxy_params').proxy_url)
        self.assertTrue(exists_in_args('policy', args))
        self.assertTrue(exists_in_args('dummy', args))
        self.assertTrue(exists_in_args('all', args))
        mock_invoke_endpoint.assert_called_once()

    @patch('conjur_api.http.api.invoke_endpoint')
    @patch.object(Api, '_api_token', new_callable=PropertyMock)
    async def test_client_check_privilege_invokes_api(self, mock_api_token, mock_invoke_endpoint):
        mock_api_token.return_value = 'test_token'
        await self.client.check_privilege('policy', 'dummy1', 'dummy2', 'dummy3')

        args, kwargs = mock_invoke_endpoint.call_args
        self.assertEqual('test_token', kwargs.get('api_token'))
        self.assertEqual('proxy.com', kwargs.get('proxy_params').proxy_url)
        self.assertTrue(exists_in_args('policy', args))
        self.assertTrue(exists_in_args('dummy1', args))
        self.assertTrue(exists_in_args('dummy2', args))
        self.assertTrue(exists_in_args('dummy3', args))
        mock_invoke_endpoint.assert_called_once()

    @patch('aiohttp.ClientSession.request')
    async def test_client_enable_valid_authenticator(self, mock_request):
        mock_request.return_value = MockResponse('', 204)
        response = await self.client.set_authenticator_state('authn-iam/test', True)

        self.assertEqual(response, '')

    @patch('aiohttp.ClientSession.request')
    async def test_client_disable_valid_authenticator(self, mock_request):
        mock_request.return_value = MockResponse('', 204)
        response = await self.client.set_authenticator_state('authn-iam/test', False)

        self.assertEqual(response, '')

    @patch('aiohttp.ClientSession.request')
    async def test_client_enable_authenticator_no_permissions(self, mock_request):
        mock_request.return_value = MockResponse('', 403)

        with self.assertRaises(HttpError) as context:
            await self.client.set_authenticator_state('authn-iam/test', True)

    @patch('aiohttp.ClientSession.request')
    async def test_client_disable_authenticator_no_permissions(self, mock_request):
        mock_request.return_value = MockResponse('', 403)

        with self.assertRaises(HttpError) as context:
            await self.client.set_authenticator_state('authn-iam/test', False)

    @patch('aiohttp.ClientSession.request')
    async def test_client_enable_non_existing_authenticator(self, mock_request):
        mock_request.return_value = MockResponse('', 401)

        with self.assertRaises(HttpError) as context:
            await self.client.set_authenticator_state('authn-iam/test', True)

    @patch('aiohttp.ClientSession.request')
    async def test_client_disable_non_existing_authenticator(self, mock_request):
        mock_request.return_value = MockResponse('', 401)

        with self.assertRaises(HttpError) as context:
            await self.client.set_authenticator_state('authn-iam/test', False)

    @patch('aiohttp.ClientSession.request')
    async def test_client_enable_authenticator_without_service_id(self, mock_request):
        mock_request.return_value = MockResponse('', 204)
        response = await self.client.set_authenticator_state('authn-gcp', True)

        self.assertEqual(response, '')

    @patch('aiohttp.ClientSession.request')
    async def test_client_disable_authenticator_without_service_id(self, mock_request):
        mock_request.return_value = MockResponse('', 204)
        response = await self.client.set_authenticator_state('authn-gcp', False)

        self.assertEqual(response, '')

    @patch('aiohttp.ClientSession.request')
    async def test_client_proxy_params_passed_to_auth_enablement(self, mock_request):
        mock_request.return_value = MockResponse('', 204)
        response = await self.client.set_authenticator_state('authn-iam/test', True)

        self.assertEqual(response, '')
        args, kwargs = mock_request.call_args
        self.assertEqual('proxy.com', kwargs.get('proxy'))

    @patch('conjur_api.providers.oidc_authentication_strategy.invoke_endpoint')
    @patch('conjur_api.http.api.invoke_endpoint')
    async def test_oidc_authentication(self, mock_regular_invoke_endpoint, mock_auth_invoke_endpoint):
        await self.oidc_client.authenticate()

        args, kwargs = mock_auth_invoke_endpoint.call_args
        self.assertTrue(exists_in_args('url', args))
        self.assertTrue(exists_in_args('service_id', args))
        self.assertTrue(exists_in_args('account', args))
        self.assertTrue(exists_in_args('id_token', args))
        self.assertEqual('proxy.com', kwargs.get('proxy_params').proxy_url)
        mock_auth_invoke_endpoint.assert_called_once()
