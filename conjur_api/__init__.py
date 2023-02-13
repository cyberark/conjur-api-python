"""
conjur_api

Package containing classes that are responsible for communicating with the Conjur server
"""
# There is no need to update the version here manually.
# It will be updated automatically in the pipeline
# based on the latest changelog version.
__version__ = "0.0-dev"

from conjur_api.client import Client
from conjur_api.interface import CredentialsProviderInterface
from conjur_api.interface import AuthenticationStrategyInterface
from conjur_api import models
from conjur_api import errors
from conjur_api import providers
