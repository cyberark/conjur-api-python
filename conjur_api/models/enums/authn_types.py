"""
AuthnTypes module
This module is used to represent different authentication methods.
"""

from enum import Enum


class AuthnTypes(Enum):   # pragma: no cover
    """
    Represent possible authentication methods that the cli might be using
    """
    UsernamePassword = 0
    OIDC = 1
