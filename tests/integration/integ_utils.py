from enum import Enum
from typing import Optional

from conjur_api import Client, AuthenticationStrategyInterface
from conjur_api.models import CredentialsData, SslVerificationMode
from conjur_api.models.general.conjur_connection_info \
    import ConjurConnectionInfo
from conjur_api.providers import SimpleCredentialsProvider, \
    AuthnAuthenticationStrategy, LdapAuthenticationStrategy
from conjur_api.providers.oidc_authentication_strategy \
    import OidcAuthenticationStrategy


class ConjurUser:
    def __init__(self, user_id: str, secret: str):
        self.id = user_id
        self.secret = secret


class AuthenticationStrategyType(Enum):
    AUTHN = 'AUTHN'
    LDAP = 'LDAP'
    OIDC = 'OIDC'


async def create_client(
    username: str,
    password: str,
    authn_strategy_type: Optional[AuthenticationStrategyType] =
        AuthenticationStrategyType.AUTHN,
        service_id: Optional[str] = None
) -> Client:
    # When running locally change to https://0.0.0.0:443
    conjur_url = "https://conjur-https"
    account = "dev"
    conjur_data = ConjurConnectionInfo(
        conjur_url=conjur_url,
        account=account,
        service_id=service_id
    )
    credentials_provider = SimpleCredentialsProvider()
    credentials = CredentialsData(
        username=username,
        password=password,
        machine=conjur_url
    )

    credentials_provider.save(credentials)

    authn_strategy: AuthenticationStrategyInterface
    if authn_strategy_type == AuthenticationStrategyType.OIDC:
        authn_strategy = OidcAuthenticationStrategy(credentials_provider)
    elif authn_strategy_type == AuthenticationStrategyType.LDAP:
        authn_strategy = LdapAuthenticationStrategy(credentials_provider)
    else:
        authn_strategy = AuthnAuthenticationStrategy(credentials_provider)

    return Client(conjur_data, authn_strategy=authn_strategy,
                  ssl_verification_mode=SslVerificationMode.INSECURE)
