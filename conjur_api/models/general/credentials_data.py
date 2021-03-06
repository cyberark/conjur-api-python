# -*- coding: utf-8 -*-

"""
CredentialsData module

This module represents the DTO that holds credential data
"""


# pylint: disable=too-few-public-methods
class CredentialsData:
    """
    Used for setting user input data to login to Conjur
    """

    def __init__(self, machine: str = None, username: str = None, password: str = None, api_key: str = None):
        self.machine = machine
        self.username = username
        self.password = password
        self.api_key = api_key

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
