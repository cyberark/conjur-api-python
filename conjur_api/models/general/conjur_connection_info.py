# -*- coding: utf-8 -*-

"""
ConjurConnectionInfo module

This module represents an object that holds the connection data
"""


# pylint: disable=too-few-public-methods
# pylint: disable=too-many-arguments

class ConjurConnectionInfo:
    """
    Used for setting user input data
    """

    def __init__(self, conjur_url: str = None, account: str = None, cert_file: str = None, service_id: str = None,
                 authn_type: int = 0):
        self.conjur_url = conjur_url
        self.conjur_account = account
        self.cert_file = cert_file
        self.service_id = service_id
        self.authn_type = authn_type

    def __repr__(self) -> str:
        return f"{self.__dict__}"
