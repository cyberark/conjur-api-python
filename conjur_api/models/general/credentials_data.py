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

    def api_token_expiration_datetime(self) -> datetime:
        """
        Method to get the API token expiration in datetime
        """
        return datetime.strptime(self.api_token_expiration, EXPIRATION_FORMAT)

    @staticmethod
    def convert_expiration_datetime_to_str(api_token_expiration: datetime) -> str:
        """
        Method to convert the API token expiration from datetime to str
        """
        return api_token_expiration.strftime(EXPIRATION_FORMAT)
