"""
Utils module

This module holds common logic across the codebase
"""
import base64
import json
import platform
from datetime import datetime, timedelta

from conjur_api.errors.errors import MissingRequiredParameterException
from conjur_api.models.enums.os_types import OSTypes


def list_dictify(obj):
    """
    Function for building a dictionary from all attributes that have values
    """
    list_dict = {}
    for attr, value in obj.__dict__.items():
        if value:
            list_dict[str(attr)] = value

    return list_dict


def get_param(name: str, **kwargs):
    """
    Return value of name if name in kwargs; None otherwise.
    Throws MissingRequiredParameterException in case kwargs is empty or not
    provided
    """
    if len(kwargs) == 0:
        raise MissingRequiredParameterException('arg_params is empty')
    return kwargs[name] if name in kwargs else None


def get_current_os() -> OSTypes:  # pragma: no cover
    """
    Determine which os we currently use
    """
    if platform.system() == "Darwin":
        return OSTypes.MAC_OS
    if platform.system() == "Linux":
        return OSTypes.LINUX
    if platform.system() == "Windows":
        return OSTypes.WINDOWS
    return OSTypes.UNKNOWN

# Tokens should only be reused for 5 minutes (max lifetime is 8 minutes)
DEFAULT_TOKEN_EXPIRATION = 8
API_TOKEN_SAFETY_BUFFER = 3
DEFAULT_API_TOKEN_DURATION = DEFAULT_TOKEN_EXPIRATION - API_TOKEN_SAFETY_BUFFER

def calculate_token_expiration(api_token: str) -> datetime:
    """
    Attempt to get the expiration from the token.
    If that fails, the default expiration will be used.

    Args:
        api_token: The API token to calculate expiration for.

    Returns:
        The calculated expiration datetime.
    """
    # Attempt to get the expiration from the token. If failing then the default expiration will be used
    try:
        # The token is in JSON format. Each field in the token is base64 encoded.
        # So we decode the payload filed and then extract the expiration date from it
        decoded_token_payload = base64.b64decode(json.loads(api_token)['payload'].encode('ascii'))
        token_expiration = json.loads(decoded_token_payload)['exp']
        return datetime.fromtimestamp(token_expiration) - timedelta(minutes=API_TOKEN_SAFETY_BUFFER)
    except Exception:
        # If we can't extract the expiration from the token because we work with an older version
        # of Conjur, then we use the default expiration
        return datetime.now() + timedelta(minutes=DEFAULT_API_TOKEN_DURATION)
