# -*- coding: utf-8 -*-

"""
CredentialsData module

This module represents the DTO that holds credential data
"""


# pylint: disable=too-few-public-methods
from datetime import datetime

EXPIRATION_FORMAT = "%Y-%m-%d %H:%M:%S"


class CredentialsData:
    """
    Used for setting user input data to login to Conjur
    """

    # pylint: disable=too-many-arguments
    def __init__(self, machine: str = None, username: str = None, password: str = None, api_key: str = None,
                 api_token: str = None, api_token_expiration: str = None):
        self.machine = machine
        self.username = username
        self.password = password
        self.api_key = api_key
        self.api_token = api_token
        self.api_token_expiration = api_token_expiration

    @classmethod
    def convert_dict_to_obj(cls, dic: dict):
        """
        Method to convert dictionary to object
        """
        return CredentialsData(**dic)

    # pylint: disable=line-too-long
    def __repr__(self):
        return f"{{'machine': '{self.machine}', 'username': '{self.username}', 'password': '****', 'api_key': '****'}}"

    def __eq__(self, other) -> bool:
        """
        Method for comparing resources by their values and not by reference
        """
        return self.machine == other.machine and self.username == other.username and self.password == \
               other.password and self.api_key == other.api_key

    @staticmethod
    def expiration_str_to_datetime(api_token_expiration: str) -> datetime:
        return datetime.strptime(api_token_expiration, EXPIRATION_FORMAT)

    @staticmethod
    def expiration_datetime_to_str(api_token_expiration: datetime) -> str:
        return api_token_expiration.strftime(EXPIRATION_FORMAT)
