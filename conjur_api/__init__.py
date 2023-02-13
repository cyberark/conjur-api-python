"""
conjur_api

Package containing classes that are responsible for communicating with the Conjur server
"""
__version__ = "5.0.12"

from conjur_api.client import Client
from conjur_api.interface import CredentialsProviderInterface
from conjur_api.interface import AuthenticationStrategyInterface
from conjur_api import models
from conjur_api import errors
from conjur_api import providers
