"""
AuthnTypes module
This module is used to represent different authentication methods.
"""

from enum import Enum


class AuthnTypes(Enum):  # pragma: no cover
    """
    Represent possible authentication methods that the CLI might be using
    """
    PROVIDED_TOKEN = 0
    AUTHN = 1
