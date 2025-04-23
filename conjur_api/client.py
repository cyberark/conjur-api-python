# -*- coding: utf-8 -*-

"""
Client module

This module is used to setup an API client that will be used fo interactions with
the Conjur server
"""

# Builtins
import json
import logging
from typing import Optional, Tuple

from conjur_api.errors.errors import ResourceNotFoundException, MissingRequiredParameterException, HttpStatusError
from conjur_api.http.api import Api
from conjur_api.interface.authentication_strategy_interface import AuthenticationStrategyInterface
# Internals
from conjur_api.models import SslVerificationMode, CreateHostData, CreateTokenData, ListMembersOfData, \
    ListPermittedRolesData, ConjurConnectionInfo, Resource, CredentialsData
from conjur_api.utils.decorators import allow_sync_invocation
from conjur_api.wrappers.http_wrapper import set_telemetry_header_value
from importlib.metadata import version, PackageNotFoundError

LOGGING_FORMAT = '%(asctime)s %(levelname)s: %(message)s'
LOGGING_FORMAT_WARNING = 'WARNING: %(message)s'

logger = logging.getLogger(__name__)

@allow_sync_invocation()
# pylint: disable=too-many-public-methods
class Client:
    """
    Client

    This class is used to construct a client for API interaction
    """
    integration_name = 'SecretsManagerPython SDK'
    try:
        integration_version = version("conjur_api")
    except PackageNotFoundError:
        integration_version = 'No Version Found'
    integration_type = 'cybr-secretsmanager'
    vendor_name = 'CyberArk'
    vendor_version = None

    def set_telemetry_header(self):
        """
        Build http header
        """
        final_telemetry_header = ""

        final_telemetry_header += "in=" + Client.integration_name
        final_telemetry_header += "&it=" + Client.integration_type
        final_telemetry_header += "&iv=" + Client.integration_version

        final_telemetry_header += "&vn=" + Client.vendor_name
        if Client.vendor_version is not None:
            final_telemetry_header += "&vv=" + Client.vendor_version

        set_telemetry_header_value(final_telemetry_header)

    # The method signature is long but we want to explicitly control
    # what parameters are allowed
    # pylint: disable=try-except-raise,too-many-statements,too-many-arguments
    def __init__(
            self,
            connection_info: ConjurConnectionInfo,
            ssl_verification_mode: SslVerificationMode = SslVerificationMode.TRUST_STORE,
            authn_strategy: AuthenticationStrategyInterface = None,
            debug: bool = False,
            http_debug: bool = False,
            async_mode: bool = True):
        """

        @param conjurrc_data: Connection metadata for conjur server
        @param ssl_verification_mode: Certificate validation stratagy
        @param authn_strategy:
        @param debug:
        @param http_debug:
        @param async_mode: This will make all of the class async functions run in sync mode (without need of await)
        Note that this functionality wraps the async function with 'asyncio.run'. setting this value to False
        is not allowed inside running event loop. For example, async_mode cannot be False if running inside
        'asyncio.run()'
        """
        self.configure_logger(debug)
        self.async_mode = async_mode
        if ssl_verification_mode == SslVerificationMode.INSECURE:
            # TODO remove this is a cli user facing
            logger.debug("Warning: Running the command with '--insecure' "
                          "makes your system vulnerable to security attacks")

        logger.debug("Initializing configuration...")

        self.ssl_verification_mode = ssl_verification_mode
        self.connection_info = connection_info
        self.debug = debug
        self._api = self._create_api(http_debug, authn_strategy)

        self.set_telemetry_header()
        logger.debug("Client initialized")

    def set_integration_name( self, value ):
        """
        Sets the integration name for the client and updates the telemetry header.

        This function updates the integration name value for the client and triggers an update to the
            telemetry header to reflect the change.

        Args:
            value (str): The integration name to be set for the client.
        """
        Client.integration_name = value
        self.set_telemetry_header()

    def set_integration_type( self, value ):
        """
        Sets the integration type for the client and updates the telemetry header.

        This function updates the integration type value for the client and triggers an update to the
        telemetry header to reflect the change.

        Args:
            value (str): The integration type to be set for the client.
        """
        Client.integration_type = value
        self.set_telemetry_header()

    def set_integration_version( self, value ):
        """
        Sets the integration version for the client and updates the telemetry header.

        This function updates the integration version value for the client and triggers an update to the
        telemetry header to reflect the change.

        Args:
            value (str): The integration version to be set for the client.
        """
        Client.integration_version = value
        self.set_telemetry_header()

    def set_vendor_name( self, value ):
        """
        Sets the vendor name for the client and updates the telemetry header.

        This function updates the vendor name value for the client and triggers an update to the
        telemetry header to reflect the change.

        Args:
            value (str): The vendor name to be set for the client.
        """
        Client.vendor_name = value
        self.set_telemetry_header()

    def set_vendor_version( self, value ):
        """
        Sets the vendor version for the client and updates the telemetry header.

        This function updates the vendor version value for the client and triggers an update to the
        telemetry header to reflect the change.

        Args:
            value (str): The vendor version to be set for the client.
        """
        Client.vendor_version = value
        self.set_telemetry_header()

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
        """
        Login to conjur using credentials provided to credentials provider
        @return: API key
        """
        return await self._api.login()

    async def authenticate(self) -> Tuple[str, str]:
        """
        Authenticate to conjur using credentials provided to credentials provider
        @return: API token
        """
        token, expiration = await self._api.authenticate()
        return token, CredentialsData.convert_expiration_datetime_to_str(expiration)

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

    async def check_privilege(self, kind: str, resource_id: str, privilege: str, role_id: str = None) -> bool:
        """
        Checks a privilege on a resource based on its kind, ID, role, and privilege.
        """
        return await self._api.check_privilege(kind, resource_id, privilege, role_id)

    async def get_resource(self, kind: str, resource_id: str) -> json:
        """
        Gets a resource based on its kind and ID
        """
        return await self._api.get_resource(kind, resource_id)

    async def resource_exists(self, kind: str, resource_id: str) -> bool:
        """
        Check for the existance of a resource based on its kind and ID
        """
        return await self._api.resource_exists(kind, resource_id)

    async def get_role(self, kind: str, role_id: str) -> json:
        """
        Gets a role based on its kind and ID
        """
        return await self._api.get_role(kind, role_id)

    async def role_exists(self, kind: str, role_id: str) -> bool:
        """
        Check for the existance of a role based on its kind and ID
        """
        return await self._api.role_exists(kind, role_id)

    async def role_memberships(self, kind: str, role_id: str, direct: bool = False) -> json:
        """
        Lists the memberships of a role
        """
        return await self._api.role_memberships(kind, role_id, direct)

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
        response = await self._api.create_token(create_token_data)
        return response.json

    async def create_host(self, create_host_data: CreateHostData) -> json:
        """
        Create host using the hostfactory
        """
        response = await self._api.create_host(create_host_data)
        return response.json

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

    async def set_authenticator_state(self, authenticator_id: str, enabled: bool) -> str:
        """
        Sets the authenticator state
        @note: This endpoint is part of an early implementation of support for enabling Conjur authenticators via the
               API, and is currently available at the Community (or early alpha) level. This endpoint is still subject
               to breaking changes in the future.
        """
        return await self._api.set_authenticator_state(authenticator_id, enabled)

    async def get_server_info(self):
        """
        Get the info json response from conjur.
        @note: This is a Conjur Enterprise feature only
        """
        # pylint: disable=no-else-raise
        try:
            response = await self._api.get_server_info()
            return response.json
        except HttpStatusError as err:
            if err.status == 404:
                exception_details = "get_server_info is a Conjur Enterprise feature only. Make sure " \
                                    "ConjurrcData.conjur_url is valid and you are working against " \
                                    "Conjur Enterprise server"
                raise ResourceNotFoundException(exception_details) from err
            else:
                raise

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
        return await self._find_resources_by_identifier(resource_identifier)

    async def find_resource_by_identifier(self, resource_identifier: str) -> list:
        """
        Look for a resource with the given identifier, and return its kind.
        Fail if there isn't exactly one such resource.
        """
        resources = await self._find_resources_by_identifier(resource_identifier)
        if not resources:
            raise ResourceNotFoundException(resource_identifier)
        if len(resources) > 1:
            raise MissingRequiredParameterException(
                f"Ambiguous resource identifier: {resource_identifier}. "
                f"There are multiple resources with this identifier: "
                f"({', '.join([res.full_id() for res in resources])})")

        return resources[0]

    def _create_api(self, http_debug, authn_strategy):

        return Api(
            connection_info=self.connection_info,
            ssl_verification_mode=self.ssl_verification_mode,
            authn_strategy=authn_strategy,
            debug=self.debug,
            http_debug=http_debug)

    async def _find_resources_by_identifier(self, resource_identifier: str) -> list:
        list_constraints = {"search": resource_identifier}
        returned_resources_ids = await self._api.resources_list(list_constraints)

        def get_resource_kind_if_matches(returned_resource_id):
            resource = Resource.from_full_id(returned_resource_id)
            return resource if resource.identifier == resource_identifier else None

        resources = map(get_resource_kind_if_matches, returned_resources_ids)
        resources = [res for res in resources if res]  # Remove None elements
        return resources
