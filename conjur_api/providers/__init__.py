"""
Providers module

This module holds all the providers of the SDK
"""
from conjur_api.providers.authn_authentication_strategy import \
    AuthnAuthenticationStrategy
from conjur_api.providers.aws_iam_authentication_strategy import \
    AWSIAMAuthenticationStrategy
from conjur_api.providers.azure_authentication_strategy import \
    AzureAuthenticationStrategy
from conjur_api.providers.cert_authentication_strategy import \
    CertAuthenticationStrategy
from conjur_api.providers.gcp_authentication_strategy import \
    GCPAuthenticationStrategy
from conjur_api.providers.jwt_authentication_strategy import \
    JWTAuthenticationStrategy
from conjur_api.providers.ldap_authentication_strategy import \
    LdapAuthenticationStrategy
from conjur_api.providers.oidc_authentication_strategy import \
    OidcAuthenticationStrategy
from conjur_api.providers.simple_credentials_provider import \
    SimpleCredentialsProvider
from conjur_api.providers.token_authentication_strategy import \
    TokenAuthenticationStrategy
