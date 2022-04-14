"""
AuthnTypes module
This module is used to represent different authentication methods.
"""

from enum import Enum


class AuthnTypes(Enum):  # pragma: no cover
    """
    Represent possible authentication methods that the CLI might be using
    """
    AUTHN = 0
    PROVIDED_TOKEN = 1
