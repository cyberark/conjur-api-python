import os
from enum import Enum
from typing import Optional

from conjur_api import AuthenticationStrategyInterface, Client
from conjur_api.models import CredentialsData, SslVerificationMode
from conjur_api.models.general.conjur_connection_info import \
    ConjurConnectionInfo
from conjur_api.providers import (AuthnAuthenticationStrategy,
                                  LdapAuthenticationStrategy,
                                  SimpleCredentialsProvider,
                                  TokenAuthenticationStrategy)
from conjur_api.providers.jwt_authentication_strategy import \
    JWTAuthenticationStrategy
from conjur_api.providers.oidc_authentication_strategy import \
    OidcAuthenticationStrategy


class ConjurUser:
    def __init__(self, user_id: str, secret: str):
        self.id = user_id
        self.secret = secret


class AuthenticationStrategyType(Enum):
    AUTHN = 'AUTHN'
    LDAP = 'LDAP'
    OIDC = 'OIDC'
    JWT  = 'JWT'
    TOKEN = 'TOKEN'

def _conjur_url() -> str:
    if os.getenv("TEST_CLOUD") != "true":
        return "https://conjur-https" # Running in Docker Compose

    return os.environ['CONJUR_APPLIANCE_URL'] + "/api" # Running in Conjur Cloud provisioned by Jenkins

async def create_client(username: str, password: str,
                        authn_strategy_type: Optional[AuthenticationStrategyType] = AuthenticationStrategyType.AUTHN,
                        service_id: Optional[str] = None) -> Client:
    """
    Function to create a Conjur client with the specified authentication strategy.
    """
    conjur_url = _conjur_url()
    account = "conjur"
    conjur_data = ConjurConnectionInfo(
        conjur_url=conjur_url,
        account=account,
        service_id=service_id
    )
    credentials_provider = SimpleCredentialsProvider()
    credentials = CredentialsData(username=username, machine=conjur_url)
    if authn_strategy_type == AuthenticationStrategyType.TOKEN:
        credentials.api_token = password  # For TOKEN strategy, password is the token
    else:
        credentials.password = password
    credentials_provider.save(credentials)

    authn_strategy: AuthenticationStrategyInterface
    if authn_strategy_type == AuthenticationStrategyType.OIDC:
        authn_strategy = OidcAuthenticationStrategy(credentials_provider)
    elif authn_strategy_type == AuthenticationStrategyType.JWT:
        authn_strategy = JWTAuthenticationStrategy(password) # password is the JWT token
    elif authn_strategy_type == AuthenticationStrategyType.LDAP:
        authn_strategy = LdapAuthenticationStrategy(credentials_provider)
    elif authn_strategy_type == AuthenticationStrategyType.TOKEN:
        authn_strategy = TokenAuthenticationStrategy(credentials_provider)
    else:
        authn_strategy = AuthnAuthenticationStrategy(credentials_provider)

    return Client(conjur_data, authn_strategy=authn_strategy,
                  ssl_verification_mode=SslVerificationMode.INSECURE, debug=True)

async def create_admin_client() -> Client:
    """
    Function to create a client authenticated as the admin user
    for either Conjur OSS or Cloud, based on environment variables.
    """
    # Check environment variables to determine if we are connecting to Conjur OSS or Cloud
    if os.getenv("TEST_CLOUD") != "true":
        # For Conjur OSS, use the admin user and API key provided in the environment variables
        # file deepcode ignore NoHardcodedCredentials/test: This is a test file
        # file deepcode ignore NoHardcodedPasswords/test: This is a test file
        return await create_client("admin", os.environ['CONJUR_AUTHN_API_KEY'])

    # For Conjur Cloud, use the token already retrieved by Jenkins and stored in environment variables
    return await create_client(os.environ['CONJUR_AUTHN_LOGIN'], os.environ['CONJUR_AUTHN_TOKEN'],
                               AuthenticationStrategyType.TOKEN)
