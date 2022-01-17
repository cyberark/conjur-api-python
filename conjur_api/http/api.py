# -*- coding: utf-8 -*-

"""
API module

Provides high-level interface for programmatic API interactions
"""
# Builtins
import json
import logging
from typing import Optional
from datetime import datetime, timedelta
from urllib import parse

# Internals
from conjur_api.http.endpoints import ConjurEndpoint
from conjur_api.interface.credentials_store_interface import CredentialsProviderInterface
from conjur_api.wrappers.http_response import HttpResponse
from conjur_api.wrappers.http_wrapper import HttpVerb, invoke_endpoint
from conjur_api.errors.errors import InvalidResourceException, MissingRequiredParameterException
# pylint: disable=too-many-instance-attributes
from conjur_api.models import Resource, ConjurConnectionInfo, ListPermittedRolesData, ListMembersOfData, CreateHostData, \
    CreateTokenData, SslVerificationMetadata, SslVerificationMode


# pylint: disable=unspecified-encoding,too-many-public-methods
class Api:
    """
    This module provides a high-level programmatic access to the HTTP API
    when all the needed arguments and parameters are well-known
    """
    # Tokens should only be reused for 5 minutes (max lifetime is 8 minutes)
    API_TOKEN_DURATION = 5

    KIND_VARIABLE = 'variable'
    KIND_HOSTFACTORY = 'host_factory'
    ID_FORMAT = '{account}:{kind}:{id}'
    ID_RETURN_PREFIX = '{account}:{kind}:'

    _api_token = None

    # We explicitly want to enumerate all params needed to instantiate this
    # class but this might not be needed in the future
    # pylint: disable=unused-argument,too-many-arguments
    def __init__(
            self,
            connection_info: ConjurConnectionInfo,
            credentials_provider: CredentialsProviderInterface,
            ssl_verification_mode: SslVerificationMode = SslVerificationMode.TRUST_STORE,
            debug: bool = False,
            http_debug=False,
    ):
        # Sanity checks
        self.ssl_verification_data = SslVerificationMetadata(ssl_verification_mode,
                                                             connection_info.cert_file)

        self._account = connection_info.conjur_account
        self._url = connection_info.conjur_url
        self._api_key = None
        self.credentials_provider: CredentialsProviderInterface = credentials_provider
        self.debug = debug
        self.http_debug = http_debug
        self.api_token_expiration = None
        self._login_id = None

        self._default_params = {  # TODO remove, pass to invoke endpoint ConjurConnectionInfo
            'url': self._url,
            'account': self._account
        }

        # WARNING: ONLY FOR DEBUGGING - DO NOT CHECK IN LINES BELOW UNCOMMENTED
        # from .http import enable_http_logging
        # if http_debug: enable_http_logging()

    @property
    def api_key(self) -> str:
        """
        Property returns api_key. if no api_key we try the password as sometimes
        @return: api_key
        """
        # TODO do not use password after credentials store is fixed to also store API key
        return self._api_key or self.password

    @property
    # pylint: disable=missing-docstring
    async def api_token(self) -> str:
        """
        @return: Conjur api_token
        """
        if not self._api_token or datetime.now() > self.api_token_expiration:
            logging.debug("API token missing or expired. Fetching new one...")
            self.api_token_expiration = datetime.now() + timedelta(minutes=self.API_TOKEN_DURATION)
            self._api_token = await self.authenticate()

            return self._api_token

        logging.debug("Using cached API token...")
        return self._api_token

    @property
    def password(self) -> str:
        """
        password as being saved inside credentials_provider
        @return:
        """
        return self.credentials_provider.load(self._url).password

    @property
    def login_id(self) -> str:
        """
        @return: The login_id (username)
        """
        if not self._login_id:
            self._login_id = self.credentials_provider.load(self._url).username
        return self._login_id

    async def login(self) -> str:
        """
        This method uses the basic auth login id (username) and password
        to retrieve an conjur_api key from the server that can be later used to
        retrieve short-lived conjur_api tokens.
        """
        logging.debug("Logging in to %s...", self._url)
        password = self.password
        if not password:
            raise MissingRequiredParameterException("password requires when login")
        response = await invoke_endpoint(HttpVerb.GET, ConjurEndpoint.LOGIN,
                                         self._default_params, auth=(self.login_id, password),
                                         ssl_verification_metadata=self.ssl_verification_data)
        self._api_key = response.text
        return self.api_key

    async def authenticate(self) -> str:
        """
        Authenticate uses the api_key to fetch a short-lived conjur_api token that
        for a limited time will allow you to interact fully with the Conjur
        vault.
        """
        if not self.api_key and self.login_id and self.password:
            # TODO we do this since api_key is not provided. it should be stored like username,
            # password inside credentials_data
            await self.login()

        if not self.login_id or not self.api_key:
            raise MissingRequiredParameterException("Missing parameters in "
                                                    "authentication invocation")

        params = {
            'login': self.login_id
        }
        params.update(self._default_params)

        logging.debug("Authenticating to %s...", self._url)
        response = await invoke_endpoint(
            HttpVerb.POST,
            ConjurEndpoint.AUTHENTICATE,
            params,
            self.api_key,
            ssl_verification_metadata=self.ssl_verification_data)
        return response.text

    async def resources_list(self, list_constraints: dict = None) -> dict:
        """
        This method is used to fetch all available resources for the current
        account. Results are returned as an array of identifiers.
        """
        params = {
            'account': self._account
        }
        params.update(self._default_params)

        # Remove 'inspect' from query as it is client-side param that shouldn't get to the server.
        inspect = list_constraints.pop('inspect', None) if list_constraints else None

        if list_constraints is not None:
            response = await invoke_endpoint(HttpVerb.GET, ConjurEndpoint.RESOURCES,
                                             params,
                                             query=list_constraints,
                                             api_token=await self.api_token,
                                             ssl_verification_metadata=self.ssl_verification_data)
        else:
            response = await invoke_endpoint(HttpVerb.GET, ConjurEndpoint.RESOURCES,
                                             params,
                                             api_token=await self.api_token,
                                             ssl_verification_metadata=self.ssl_verification_data)

        resources = response.json
        # Returns the result as a list of resource ids instead of the raw JSON only
        # when the user does not provide `inspect` as one of their filters
        if not inspect:
            # For each element (resource) in the resources sequence, we extract the resource id
            resource_list = map(lambda resource: resource['id'], resources)
            # TODO method signature returns dict, need to check who is expecting list
            return list(resource_list)

        # To see the full resources response see
        # https://docs.conjur.org/Latest/en/Content/Developer/Conjur_API_List_Resources.htm
        # ?tocpath=Developer%7CREST%C2%A0APIs%7C_____17
        return resources

    async def get_variable(self, variable_id: str, version: str = None) -> Optional[bytes]:
        """
        This method is used to fetch a secret's (aka "variable") value from
        Conjur vault.
        """
        params = {
            'kind': self.KIND_VARIABLE,
            'identifier': variable_id,
        }
        params.update(self._default_params)

        query_params = {}
        if version is not None:
            query_params = {
                'version': version
            }

        # pylint: disable=no-else-return
        if version is not None:
            response = await invoke_endpoint(HttpVerb.GET, ConjurEndpoint.SECRETS, params,
                                             api_token=await self.api_token, query=query_params,
                                             ssl_verification_metadata=self.ssl_verification_data)
        else:
            response = await invoke_endpoint(HttpVerb.GET, ConjurEndpoint.SECRETS, params,
                                             api_token=await self.api_token,
                                             ssl_verification_metadata=self.ssl_verification_data)
        return response.content

    async def get_variables(self, *variable_ids) -> dict:
        """
        This method is used to fetch multiple secret's (aka "variable") values from
        Conjur vault.
        """
        assert variable_ids, 'Variable IDs must not be empty!'

        full_variable_ids = []
        for variable_id in variable_ids:
            full_variable_ids.append(self.ID_FORMAT.format(account=self._account,
                                                           kind=self.KIND_VARIABLE,
                                                           id=variable_id))
        query_params = {
            'variable_ids': ','.join(full_variable_ids),
        }

        response = await invoke_endpoint(HttpVerb.GET, ConjurEndpoint.BATCH_SECRETS,
                                         self._default_params,
                                         api_token=await self.api_token,
                                         ssl_verification_metadata=self.ssl_verification_data,
                                         query=query_params,
                                         )

        variable_map = response.json

        # Remove the 'account:variable:' prefix from result's variable names
        remapped_keys_dict = {}
        prefix_length = len(self.ID_RETURN_PREFIX.format(account=self._account,
                                                         kind=self.KIND_VARIABLE))
        for variable_name, variable_value in variable_map.items():
            new_variable_name = variable_name[prefix_length:]
            remapped_keys_dict[new_variable_name] = variable_value

        return remapped_keys_dict

    async def create_token(self, create_token_data: CreateTokenData) -> HttpResponse:
        """
        This method is used to create token/s for hosts with restrictions.
        """
        if create_token_data is None:
            raise MissingRequiredParameterException('create_token_data is empty')

        create_token_data.host_factory = self.ID_FORMAT.format(account=self._account,
                                                               kind=self.KIND_HOSTFACTORY,
                                                               id=create_token_data.host_factory)

        # parse.urlencode, If any values in the query arg are sequences and doseq is true, each
        # sequence element is converted to a separate parameter.
        # This is set to True to handle CreateTokenData.cidr which is a list
        create_token_data = parse.urlencode(create_token_data.to_dict(),
                                            doseq=True)

        params = {}
        params.update(self._default_params)
        return await invoke_endpoint(HttpVerb.POST,
                                     ConjurEndpoint.HOST_FACTORY_TOKENS,
                                     params,
                                     create_token_data,
                                     api_token=await self.api_token,
                                     ssl_verification_metadata=self.ssl_verification_data,
                                     headers={'Content-Type': 'application/x-www-form-urlencoded'})

    async def create_host(self, create_host_data: CreateHostData) -> HttpResponse:
        """
        This method is used to create host using the hostfactory.
        """
        if create_host_data is None:
            raise MissingRequiredParameterException('create_host_data is empty')
        request_body_parameters = parse.urlencode(create_host_data.get_host_id())
        params = {}
        params.update(self._default_params)
        return await invoke_endpoint(HttpVerb.POST,
                                     ConjurEndpoint.HOST_FACTORY_HOSTS,
                                     params,
                                     request_body_parameters,
                                     api_token=create_host_data.token,
                                     ssl_verification_metadata=self.ssl_verification_data,
                                     decode_token=False,
                                     headers={'Content-Type': 'application/x-www-form-urlencoded'})

    async def revoke_token(self, token: str) -> HttpResponse:
        """
        This method is used to revoke a hostfactory token.
        """
        if token is None:
            raise MissingRequiredParameterException('token is empty')

        params = {}
        params.update(self._default_params)

        # add the token to the params so it will
        # get formatted in the url in invoke_endpoint
        params['token'] = token

        return await invoke_endpoint(HttpVerb.DELETE,
                                     ConjurEndpoint.HOST_FACTORY_REVOKE_TOKEN,
                                     params,
                                     api_token=await self.api_token,
                                     ssl_verification_metadata=self.ssl_verification_data)

    async def set_variable(self, variable_id: str, value: str) -> str:
        """
        This method is used to set a secret (aka "variable") to a value of
        your choosing.
        """
        params = {
            'kind': self.KIND_VARIABLE,
            'identifier': variable_id,
        }
        params.update(self._default_params)
        response = await invoke_endpoint(HttpVerb.POST, ConjurEndpoint.SECRETS, params,
                                         value, api_token=await self.api_token,
                                         ssl_verification_metadata=self.ssl_verification_data)
        return response.text

    async def _load_policy_file(
            self, policy_id: str, policy_file: str,
            http_verb: HttpVerb) -> dict:
        """
        This method is used to load, replace or update a file-based policy into the desired
        name.
        """
        params = {
            'identifier': policy_id,
        }
        params.update(self._default_params)

        with open(policy_file, 'r') as content_file:
            policy_data = content_file.read()

        response = await invoke_endpoint(http_verb, ConjurEndpoint.POLICIES, params,
                                         policy_data, api_token=await self.api_token,
                                         ssl_verification_metadata=self.ssl_verification_data)
        return response.json

    async def load_policy_file(self, policy_id: str, policy_file: str) -> dict:
        """
        This method is used to load a file-based policy into the desired
        name.
        """
        return await self._load_policy_file(policy_id, policy_file, HttpVerb.POST)

    async def replace_policy_file(self, policy_id: str, policy_file: str) -> dict:
        """
        This method is used to replace a file-based policy into the desired
        policy ID.
        """
        return await self._load_policy_file(policy_id, policy_file, HttpVerb.PUT)

    async def update_policy_file(self, policy_id: str, policy_file: str) -> dict:
        """
        This method is used to update a file-based policy into the desired
        policy ID.
        """
        return await self._load_policy_file(policy_id, policy_file, HttpVerb.PATCH)

    async def rotate_other_api_key(self, resource: Resource) -> str:
        """
        This method is used to rotate a user/host's API key that is not the current user.
        To rotate API key of the current user use rotate_personal_api_key
        """
        if resource.kind not in ('user', 'host'):
            raise InvalidResourceException("Error: Invalid resource type")

        # Attach the resource type (user or host)
        query_params = {
            'role': resource.full_id()
        }
        response = await invoke_endpoint(HttpVerb.PUT, ConjurEndpoint.ROTATE_API_KEY,
                                         self._default_params,
                                         api_token=await self.api_token,
                                         ssl_verification_metadata=self.ssl_verification_data,
                                         query=query_params)
        return response.text

    async def rotate_personal_api_key(
            self, logged_in_user: str,
            current_password: str) -> str:
        """
        This method is used to rotate a personal API key
        """
        response = await invoke_endpoint(HttpVerb.PUT, ConjurEndpoint.ROTATE_API_KEY,
                                         self._default_params,
                                         auth=(logged_in_user, current_password),
                                         ssl_verification_metadata=self.ssl_verification_data)
        return response.text

    async def change_personal_password(
            self, logged_in_user: str, current_password: str,
            new_password: str) -> str:
        """
        This method is used to change own password
        """
        response = await invoke_endpoint(HttpVerb.PUT, ConjurEndpoint.CHANGE_PASSWORD,
                                         self._default_params,
                                         new_password,
                                         auth=(logged_in_user, current_password),
                                         ssl_verification_metadata=self.ssl_verification_data
                                         )
        return response.text

    async def get_server_info(self):
        params = {
            'url': self._url
        }
        return await invoke_endpoint(HttpVerb.GET,
                                     ConjurEndpoint.INFO,
                                     params,
                                     ssl_verification_metadata=self.ssl_verification_data)
    async def whoami(self) -> dict:
        """
        This method provides dictionary of information about the user making an API request.
        """
        response = await invoke_endpoint(HttpVerb.GET, ConjurEndpoint.WHOAMI,
                                         self._default_params,
                                         api_token=await self.api_token,
                                         ssl_verification_metadata=self.ssl_verification_data)

        return response.json

    async def list_members_of_role(self, parameters: ListMembersOfData = None) -> list:
        """
        List all members of a role, both direct and indirect
        """
        if not parameters.resource or not parameters.resource.identifier:
            raise MissingRequiredParameterException("Missing required parameter, 'identifier'")

        if not parameters.resource or not parameters.resource.kind:
            raise MissingRequiredParameterException("Missing required parameter, 'kind'")

        params = {
            'account': self._account,
            'identifier': parameters.resource.identifier,
            'kind': parameters.resource.kind,
        }
        params.update(self._default_params)

        request_parameters = parameters.list_dictify()
        del request_parameters['identifier']
        del request_parameters['resource']

        # Remove 'inspect' from query as it is client-side param that shouldn't get to the server.
        inspect = request_parameters.pop('inspect', None) if request_parameters else None

        response = await invoke_endpoint(HttpVerb.GET,
                                         ConjurEndpoint.ROLES_MEMBERS_OF,
                                         params,
                                         query=request_parameters,
                                         api_token=await self.api_token,
                                         ssl_verification_metadata=self.ssl_verification_data)

        resources = response.json

        if not inspect:
            # For each element (resource) in the resources sequence, we extract the resource id
            resource_list = map(lambda resource: resource['member'], resources)
            return list(resource_list)

        return resources

    async def list_permitted_roles(self, data: ListPermittedRolesData) -> dict:
        """
        Lists the roles which have the named permission on a resource.
        """
        if not data.kind:
            raise MissingRequiredParameterException("Missing required parameter, 'kind'")

        if not data.identifier:
            raise MissingRequiredParameterException("Missing required parameter, 'identifier'")

        if not data.privilege:
            raise MissingRequiredParameterException("Missing required parameter, 'privilege'")

        params = {
            'identifier': data.identifier,
            'kind': data.kind,
            'privilege': data.privilege
        }
        params.update(self._default_params)

        response = await invoke_endpoint(HttpVerb.GET,
                                         ConjurEndpoint.RESOURCES_PERMITTED_ROLES,
                                         params,
                                         api_token=await self.api_token,
                                         ssl_verification_metadata=self.ssl_verification_data)

        return response.json
