import platform

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
