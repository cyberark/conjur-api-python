# -*- coding: utf-8 -*-

"""
Endpoints module

This module contains any classes needed for the rest of the
module to locate the required endpoints for the HTTP API
"""

from enum import Enum


class ConjurEndpoint(Enum):
    """
    ConjurEndpoint enumerates all endpoints that are required for
    API interactions with the Conjur instance along with any
    required parameters for the paths
    """
    AUTHENTICATE = "{url}/authn/{account}/{login}/authenticate"
    AUTHENTICATE_LDAP = "{url}/authn-ldap/{service_id}/{account}/{login}/authenticate"
    LOGIN = "{url}/authn/{account}/login"
    LOGIN_LDAP = "{url}/authn-ldap/{service_id}/{account}/login"
    INFO = "{url}/info"
    POLICIES = "{url}/policies/{account}/policy/{identifier}"
    BATCH_SECRETS = "{url}/secrets"
    SECRETS = "{url}/secrets/{account}/{kind}/{identifier}"
    PRIVILEGE = "{url}/resources/{account}/{kind}/{identifier}?check=true&role={role}&privilege={privilege}"
    RESOURCES = "{url}/resources/{account}"
    RESOURCE = "{url}/resources/{account}/{kind}/{identifier}"
    ROTATE_API_KEY = "{url}/authn/{account}/api_key"
    CHANGE_PASSWORD = "{url}/authn/{account}/password"
    WHOAMI = "{url}/whoami"
    HOST_FACTORY_TOKENS = "{url}/host_factory_tokens"
    HOST_FACTORY_REVOKE_TOKEN = "{url}/host_factory_tokens/{token}"
    HOST_FACTORY_HOSTS = "{url}/host_factories/hosts"
    ROLE = "{url}/roles/{account}/{kind}/{identifier}"
    ROLES_MEMBERS_OF = "{url}/roles/{account}/{kind}/{identifier}?members"
    ROLES_MEMBERSHIPS = "{url}/roles/{account}/{kind}/{identifier}?{membership}"
    RESOURCES_PERMITTED_ROLES =\
        "{url}/resources/{account}/{kind}/{identifier}?permitted_roles=true&privilege={privilege}"
