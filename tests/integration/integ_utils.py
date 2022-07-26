from conjur_api import Client
from conjur_api.models import CredentialsData, SslVerificationMode
from conjur_api.models.general.conjur_connection_info import ConjurConnectionInfo
from conjur_api.providers import SimpleCredentialsProvider


async def create_client(username: str, password: str) -> Client:

    conjur_url = "https://conjur-https"  # When running locally change to https://0.0.0.0:443
    account = "dev"
    conjur_data = ConjurConnectionInfo(
        conjur_url=conjur_url,
        account=account
    )
    credentials_provider = SimpleCredentialsProvider()
    credentials = CredentialsData(username=username, password=password, machine=conjur_url)
    credentials_provider.save(credentials)
    return Client(conjur_data, credentials_provider=credentials_provider,
                  ssl_verification_mode=SslVerificationMode.INSECURE)