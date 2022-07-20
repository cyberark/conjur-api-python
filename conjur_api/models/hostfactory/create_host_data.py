# -*- coding: utf-8 -*-

"""
CreateHostData module

This module represents the DTO that holds the params the user passes in.
We use this DTO to build the hostfactory create host request
"""

# pylint: disable=too-many-arguments,too-few-public-methods
from conjur_api.errors.errors import MissingRequiredParameterException


class CreateHostData:
    """
    Used for organizing the params the user passed in to execute the CreateHost command
    """

    def __init__(self,
                 # using id shadows the internal id
                 host_id: str = "",
                 token: str = "",
                 annotations: dict = None):
        self.host_id = host_id
        self.token = token
        self.annotations = annotations or {}

        if self.host_id.strip() == "":
            raise MissingRequiredParameterException("Missing required parameter, 'host_id'")

        if self.token == "":
            raise MissingRequiredParameterException("Missing required parameter, 'token'")

    def get_host_id(self) -> dict:
        """
        to_dict

        This method enable aliasing 'host_id' to 'id' as the server expects
        """
        params = {
            'id': self.host_id
        }

        return params

    def get_annotations(self) -> dict:
        """
        :return: dictionary containing annotations in a format acceptable by Conjur REST API
        """
        return {
            f"annotations[{key}]": value for key, value in self.annotations.items()
        }

    def __repr__(self) -> str:
        return f"{{'id': '{self.host_id}', 'annotations': '{self.annotations}'"
