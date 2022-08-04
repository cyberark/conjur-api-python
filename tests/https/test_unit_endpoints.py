import unittest

from conjur_api.http.endpoints import ConjurEndpoint


class EndpointsTest(unittest.TestCase):
    def test_endpoint_has_correct_authenticate_template_string(self):
        auth_endpoint = ConjurEndpoint.AUTHENTICATE.value.format(url='http://host',
                                                                 account='myacct',
                                                                 login='mylogin')
        self.assertEqual(auth_endpoint, 'http://host/authn/myacct/mylogin/authenticate')

    def test_endpoint_has_correct_info_template_string(self):
        info_endpoint = ConjurEndpoint.INFO.value.format(url='https://host')
        self.assertEqual(info_endpoint, 'https://host/info')

    def test_endpoint_has_correct_login_template_string(self):
        auth_endpoint = ConjurEndpoint.LOGIN.value.format(url='http://host',
                                                             account='myacct')
        self.assertEqual(auth_endpoint, 'http://host/authn/myacct/login')

    def test_endpoint_has_correct_secrets_template_string(self):
        auth_endpoint = ConjurEndpoint.SECRETS.value.format(url='http://host',
                                                            account='myacct',
                                                            kind='varkind',
                                                            identifier='varid')
        self.assertEqual(auth_endpoint, 'http://host/secrets/myacct/varkind/varid')

    def test_endpoint_has_correct_batch_secrets_template_string(self):
        batch_endpoint = ConjurEndpoint.BATCH_SECRETS.value.format(url='http://host')
        self.assertEqual(batch_endpoint, 'http://host/secrets')

    def test_endpoint_has_correct_policy_template_string(self):
        auth_endpoint = ConjurEndpoint.POLICIES.value.format(url='http://host',
                                                             account='myacct',
                                                             identifier='polid')
        self.assertEqual(auth_endpoint, 'http://host/policies/myacct/policy/polid')

    def test_endpoint_has_correct_resources_template_string(self):
        auth_endpoint = ConjurEndpoint.RESOURCES.value.format(url='http://host',
                                                             account='myacct')
        self.assertEqual(auth_endpoint, 'http://host/resources/myacct')

    def test_endpoint_has_correct_resource_template_string(self):
        endpoint = ConjurEndpoint.RESOURCE.value.format(url='http://host',
                                                             account='myacct',
                                                             kind='varkind',
                                                             identifier='varid')
        self.assertEqual(endpoint, 'http://host/resources/myacct/varkind/varid')

    def test_endpoint_has_correct_whoami_template_string(self):
        auth_endpoint = ConjurEndpoint.WHOAMI.value.format(url='http://host',
                                                             account='myacct')
        self.assertEqual(auth_endpoint, 'http://host/whoami')

    def test_endpoint_has_correct_role_template_string(self):
        endpoint = ConjurEndpoint.ROLE.value.format(url='http://host',
                                                             account='myacct',
                                                             kind='rolekind',
                                                             identifier='roleid')
        self.assertEqual(endpoint, 'http://host/roles/myacct/rolekind/roleid')

    def test_endpoint_has_correct_role_memberships_all_template_string(self):
        endpoint = ConjurEndpoint.ROLES_MEMBERSHIPS.value.format(url='http://host',
                                                             account='myacct',
                                                             kind='rolekind',
                                                             identifier='roleid',
                                                             membership='all')
        self.assertEqual(endpoint, 'http://host/roles/myacct/rolekind/roleid?all')
