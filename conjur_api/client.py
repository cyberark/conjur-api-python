# -*- coding: utf-8 -*-

"""
Client module

This module is used to setup an API client that will be used fo interactions with
the Conjur server
"""

# Builtins
import json
import logging
from typing import Optional

# Internals
from conjur_api.models import SslVerificationMode, CreateHostData, CreateTokenData, ListMembersOfData, \
    ListPermittedRolesData, ConjurrcData, Resource
from conjur_api.errors.errors import ResourceNotFoundException, MissingRequiredParameterException
from conjur_api.interface.credentials_store_interface import CredentialsProviderInterface
from conjur_api.http.api import Api
from conjur_api.utils.decorators import allow_sync_invocation, allow_sync_mode

LOGGING_FORMAT = '%(asctime)s %(levelname)s: %(message)s'
LOGGING_FORMAT_WARNING = 'WARNING: %(message)s'


@allow_sync_invocation()
class Client:
    """
    Client

    This class is used to construct a client for API interaction
    """

    # The method signature is long but we want to explicitly control
    # what parameters are allowed
    # pylint: disable=try-except-raise,too-many-statements
    def __init__(
            self,
            conjurrc_data: ConjurrcData,
            ssl_verification_mode: SslVerificationMode = SslVerificationMode.TRUST_STORE,
            credentials_provider: CredentialsProviderInterface = None,
            debug: bool = False,
            http_debug: bool = False,
            async_mode: bool = True):

        self.configure_logger(debug)
        self.async_mode = async_mode
        if ssl_verification_mode == SslVerificationMode.INSECURE:
            # TODO remove this is a cli user facing
            logging.debug("Warning: Running the command with '--insecure' "
                          "makes your system vulnerable to security attacks")

        logging.debug("Initializing configuration...")

        self.ssl_verification_mode = ssl_verification_mode
        self.conjurrc_data = conjurrc_data
        self.debug = debug
        self._api = self._create_api(http_debug, credentials_provider)

        logging.debug("Client initialized")

    @staticmethod
    def configure_logger(debug: bool):
        """
        Configures the logging for the client
        """
        # Suppress third party logs
        if debug:
            logging.basicConfig(level=logging.DEBUG, format=LOGGING_FORMAT)
        else:
            logging.basicConfig(level=logging.WARN, format=LOGGING_FORMAT_WARNING)

    ### API passthrough
    async def login(self) -> str:
        return await self._api.login()

    async def whoami(self) -> dict:
        """
        Provides dictionary of information about the user making an API request
        """
        return await self._api.whoami()

    # Constraints remain an optional parameter for backwards compatibility in the SDK
    async def list(self, list_constraints: dict = None) -> dict:
        """
        Lists all available resources
        """
        return await self._api.resources_list(list_constraints)

    async def list_permitted_roles(self, list_permitted_roles_data: ListPermittedRolesData) -> dict:
        """
        Lists the roles which have the named permission on a resource.
        """
        return await self._api.list_permitted_roles(list_permitted_roles_data)

    async def list_members_of_role(self, data: ListMembersOfData) -> dict:
        """
        Lists the roles which have the named permission on a resource.
        """
        return await self._api.list_members_of_role(data)

    async def get(self, variable_id: str, version: str = None) -> Optional[bytes]:
        """
        Gets a variable value based on its ID
        """
        return await self._api.get_variable(variable_id, version)

    async def get_many(self, *variable_ids) -> Optional[bytes]:
        """
        Gets multiple variable values based on their IDs. Returns a
        dictionary of mapped values.
        """
        return await self._api.get_variables(*variable_ids)

    async def create_token(self, create_token_data: CreateTokenData) -> json:
        """
        Create token/s for hosts with restrictions
        """
        return await self._api.create_token(create_token_data).json

    async def create_host(self, create_host_data: CreateHostData) -> json:
        """
        Create host using the hostfactory
        """
        return await self._api.create_host(create_host_data).json

    async def revoke_token(self, token: str) -> int:
        """
        Revokes the given token
        """
        res = await self._api.revoke_token(token)
        return res.status

    async def set(self, variable_id: str, value: str) -> str:
        """
        Sets a variable to a specific value based on its ID
        """
        await self._api.set_variable(variable_id, value)

    async def load_policy_file(self, policy_name: str, policy_file: str) -> dict:
        """
        Applies a file-based policy to the Conjur instance
        """
        return await self._api.load_policy_file(policy_name, policy_file)

    async def replace_policy_file(self, policy_name: str, policy_file: str) -> dict:
        """
        Replaces a file-based policy defined in the Conjur instance
        """
        return await self._api.replace_policy_file(policy_name, policy_file)

    async def update_policy_file(self, policy_name: str, policy_file: str) -> dict:
        """
        Replaces a file-based policy defined in the Conjur instance
        """
        return await self._api.update_policy_file(policy_name, policy_file)

    async def rotate_other_api_key(self, resource: Resource) -> str:
        """
        Rotates a API keys and returns new API key
        """
        return await self._api.rotate_other_api_key(resource)

    async def rotate_personal_api_key(self, logged_in_user: str, current_password: str) -> str:
        """
        Rotates personal API keys and returns new API key
        """
        return await self._api.rotate_personal_api_key(logged_in_user, current_password)

    async def change_personal_password(
            self, logged_in_user: str, current_password: str,
            new_password: str) -> str:
        """
        Change personal password of logged-in user
        """
        # pylint: disable=line-too-long
        return await self._api.change_personal_password(logged_in_user, current_password, new_password)

    async def find_resources_by_identifier(self, resource_identifier: str) -> list:
        """
        Get all the resources with the given identifier.
        """
        list_constraints = {"search": resource_identifier}
        returned_resources_ids = await self.list(list_constraints)

        def get_resource_kind_if_matches(returned_resource_id):
            resource = Resource.from_full_id(returned_resource_id)
            return resource if resource.identifier == resource_identifier else None

        resources = map(get_resource_kind_if_matches, returned_resources_ids)
        resources = [res for res in resources if res]  # Remove None elements
        return resources

    async def find_resource_by_identifier(self, resource_identifier: str) -> list:
        """
        Look for a resource with the given identifier, and return its kind.
        Fail if there isn't exactly one such resource.
        """
        resources = await self.find_resources_by_identifier(resource_identifier)
        if not resources:
            raise ResourceNotFoundException(resource_identifier)
        if len(resources) > 1:
            raise MissingRequiredParameterException(
                f"Ambiguous resource identifier: {resource_identifier}. "
                f"There are multiple resources with this identifier: "
                f"({', '.join([res.full_id() for res in resources])})")

        return resources[0]

    def _create_api(self, http_debug, credentials_provider):

        credential_location = credentials_provider.get_store_location()
        logging.debug(f"Attempting to retrieve credentials from the '{credential_location}'...")
        logging.debug(f"Successfully retrieved credentials from the '{credential_location}'")

        return Api(
            conjurrc_data=self.conjurrc_data,
            ssl_verification_mode=self.ssl_verification_mode,
            credentials_provider=credentials_provider,
            debug=self.debug,
            http_debug=http_debug)
