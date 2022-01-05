# -*- coding: utf-8 -*-

"""
ConjurrcData module

This module represents an object that holds conjurrc data
"""


# pylint: disable=too-few-public-methods


class ConjurrcData:
    """
    Used for setting user input data
    """

    def __init__(self, conjur_url: str = None, account: str = None, cert_file: str = None):
        self.conjur_url = conjur_url
        self.conjur_account = account
        self.cert_file = cert_file

    def __repr__(self) -> str:
        return f"{self.__dict__}"
