# -*- coding: utf-8 -*-

"""
ConjurConnectionInfo module

This module represents an object that holds the connection data
"""

# pylint: disable=too-few-public-methods,too-many-arguments

from conjur_api.models.general.proxy_params import ProxyParams


class ConjurConnectionInfo:
    """
    Used for setting user input data
    """

    def __init__(self, conjur_url: str = None, account: str = None, cert_file: str = None, service_id: str = None,
                 proxy_params: ProxyParams = None):
        self.conjur_url = conjur_url
        self.conjur_account = account
        self.cert_file = cert_file
        self.service_id = service_id
        self.proxy_params = proxy_params

    def __repr__(self) -> str:
        return f"{self.__dict__}"
