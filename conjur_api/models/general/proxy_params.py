"""
ProxyParams module

This class represents an object that holds the proxy parameters
"""
# pylint: disable=too-few-public-methods

class ProxyParams:
    """
    Used for setting proxy parameters
    """

    def __init__(self, proxy_url: str):
        self.proxy_url = proxy_url

    def __repr__(self) -> str:
        return f"{self.__dict__}"
