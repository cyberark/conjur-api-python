# Conjur Python SDK

An API client for Conjur written in python.

Find more SDKs [from CyberArk](https://github.com/cyberark).

## Certification level

![](https://img.shields.io/badge/Certification%20Level-Community-28A745?link=https://github.com/cyberark/community/blob/master/Conjur/conventions/certification-levels.md)

This repo is a **Community** level project. It's a community contributed project that **is not reviewed or supported by
CyberArk**. For more detailed information on our certification levels,
see [our community guidelines](https://github.com/cyberark/community/blob/master/Conjur/conventions/certification-levels.md#community)
.

## Requirements

This project requires a working Conjur server

It officially requires python 3.10 and above but can run with lower versions compiled with openssl 1.1.1

## How to use the client

### Prerequisites

It is assumed that Conjur (OSS or Enterprise) have already been installed in the environment and running in the
background. If you haven't done so, follow these instructions for installation of
the [OSS](https://docs.conjur.org/Latest/en/Content/OSS/Installation/Install_methods.htm) and these for installation
of [Enterprise](https://docs.cyberark.com/Product-Doc/OnlineHelp/AAM-DAP/Latest/en/Content/HomeTilesLPs/LP-Tile2.htm).

Once Conjur is running in the background, you are ready to start setting up your python app to work with our Conjur
python API!

### Installation

The SDK can be installed via PyPI. Note that the SDK is a **Community level** project meaning that the SDK is subject to
alterations that may result in breaking change.

```sh

pip3 install conjur

```

To avoid unanticipated breaking changes, make sure that you stay up-to-date on our latest releases and review the
project's [CHANGELOG.md](CHANGELOG.md).

Alternatively, you can install the library from the source. Note that this will install the latest work from the cloned
source and not necessarily an official release.

If you wish to install the library from the source clone the [project](https://github.com/cyberark/conjur-api-python) and run:

```sh

pip3 install .

```

### Configuring the client

#### Define connection parameters

In order to login to conjur you need to have 5 parameters known from advance.

```python
conjur_url = "https://my_conjur.com"
account = "my_account"
username = "user1"
password = "SomeStr@ngPassword!1"
ssl_verification_mode = SslVerificationMode.TRUST_STORE
```

#### Define ConjurConnectionInfo

ConjurConnectionInfo is a data class containing all the non-credentials connection details.

```python
connection_info = ConjurConnectionInfo(conjur_url=conjur_url,account=account,cert_file=None,service_id="ldap-service-id")
```

* conjur_url - url of conjur server
* account - the account which we want to connect to
* cert_file - a path to conjur rootCA file. we need it if we initialize the client in `SslVerificationMode.SELF_SIGN`
  or `SslVerificationMode.CA_BUNDLE` mode
* service_id - a service id for the Conjur authenticator. Required when using the ldap authenticator (see below) but not when using the default `authn` authenticator.

#### Create credentials provider

The client uses credentials provider in order to get the connection credentials before making api command. This approach
allow to keep the credentials in a safe location and provide it to the client on demand.

We provide the user with `CredentialsProviderInterface` which can be implemented the way the user see as best
fit (`keyring` usage for example)

We also provide the user with a simple implementation of such provider called `SimpleCredentialsProvider`. Example of
creating such provider + storing credentials:

```python
credentials = CredentialsData(username=username, password=password, machine=conjur_url)
credentials_provider = SimpleCredentialsProvider()
credentials_provider.save(credentials)
del credentials
```

#### Create authentication strategy

The client also uses an authentication strategy in order to authenticate to conjur. This approach allows us to implement different authentication strategies
(e.g. `authn`, `authn-ldap`, `authn-k8s`) and to keep the authentication logic separate from the client implementation.

We provide the `AuthnAuthenticationStrategy` for the default Conjur authenticator. Example use:

```python
authn_provider = AuthnAuthenticationStrategy(credentials_provider)
```

We also provide the `LdapAuthenticationStrategy` for the ldap authenticator. Example use:

```python
authn_provider = LdapAuthenticationStrategy(credentials_provider)
```

When using the `LdapAuthenticationStrategy` make sure `connection_info` has a `service_id` specified.

#### Creating the client and use it

Now that we have created `connection_info` and `authn_provider`, we can create our client:

```python
client = Client(connection_info,
                authn_strategy=authn_provider,
                ssl_verification_mode=ssl_verification_mode)
```

* ssl_verification_mode = `SslVerificationMode` enum that states what is the certificate verification technique we will
  use when making the api request

After creating the client we can login to conjur and start using it. Example of usage:

```python
client.login() # login to conjur and return the api_key
client.list() # get list of all conjur resources that the user authorize to read
```

## Supported Client methods

#### `get(variable_id)`

Gets a variable value based on its ID. Variable is binary data that should be decoded to your system's encoding. For example: 
`get(variable_id).decode('utf-8')`.

#### `get_many(variable_id[,variable_id...])`

Gets multiple variable values based on their IDs. Variables are returned in a dictionary that maps the variable name to
its value.

#### `set(variable_id, value)`

Sets a variable to a specific value based on its ID.

Note: Policy to create the variable must have already been loaded, otherwise you will get a 404 error during invocation.

#### `load_policy_file(policy_name, policy_file)`

Applies a file-based YAML to a named policy. This method only supports additive changes. Result is a dictionary object
constructed from the returned JSON data.

#### `replace_policy_file(policy_name, policy_file)`

Replaces a named policy with one from the provided file. This is usually a destructive invocation. Result is a
dictionary object constructed from the returned JSON data.

#### `update_policy_file(policy_name, policy_file)`

Modifies an existing Conjur policy. Data may be explicitly deleted using the `!delete`, `!revoke`, and `!deny`
statements. Unlike
"replace" mode, no data is ever implicitly deleted. Result is a dictionary object constructed from the returned JSON
data.

#### `list(list_constraints)`

Returns a list of all available resources for the current account.

The 'list constraints' parameter is optional and should be provided as a dictionary.

For example: `client.list({'kind': 'user', 'inspect': True})`

| List constraints | Explanation                                                  |
| ---------------- | ------------------------------------------------------------ |
| kind             | Filter resources by specified kind (user, host, layer, group, policy, variable, or webservice) |
| limit            | Limit list of resources to specified number                  |
| offset           | Skip specified number of resources                           |
| role             | Retrieve list of resources that specified role is entitled to see (must specify role's full ID) |
| search           | Search for resources based on specified query                |
| inspect          | List the metadata for resources                              |

#### `get_resource(kind, resource_id)`

Gets a resource based on its kind and ID. Resource is json data that contains metadata about the resource.

#### `resource_exists(kind, resource_id)`

Check the existence of a resource based on its kind and ID. Returns a boolean.

#### `get_role(kind, role_id)`

Gets a role based on its kind and ID. Role is json data that contains metadata about the role.

#### `role_exists(kind, resource_id)`

Check the existence of a role based on its kind and ID. Returns a boolean.

#### `role_memberships(kind, role_id)`

Gets a role's memberships based on its kind and ID. Returns a list of all roles recursively inherited by this role.

#### `def list_permitted_roles(list_permitted_roles_data: ListPermittedRolesData)`

Lists the roles which have the named permission on a resource.

#### `def list_members_of_role(data: ListMembersOfData)`

Lists the resources which are members of the given resource.

#### `def create_token(create_token_data: CreateTokenData)`

Creates Host Factory tokens for creating hosts

#### `def create_host(create_host_data: CreateHostData)`

Uses Host Factory token to create host

#### `def revoke_token(token: str)`

Revokes the given Host Factory token

#### `rotate_other_api_key(resource: Resource)`

Rotates another entity's API key and returns it as a string.

Note: resource is of type Resource which should have `type` (user / host) and
`name` attributes.

#### `rotate_personal_api_key(logged_in_user, current_password)`

Rotates the personal API key of the logged-in user and returns it as a string.

#### `change_personal_password(logged_in_user, current_password, new_password)`

Updates the current, logged-in user's password with the password parameter provided.

Note: the new password must meet the Conjur password complexity constraints. It must contain at least 12 characters: 2
uppercase, 2 lowercase, 1 digit, 1 special character.

#### `whoami()`

_Note: This method requires Conjur v1.9+_

Returns a Python dictionary of information about the client making an API request (such as its IP address, user,
account, token expiration date, etc).

## Contributing

We welcome contributions of all kinds to this repository. For instructions on how to get started and descriptions of our
development workflows, please see our [contributing guide](CONTRIBUTING.md).

## License

Copyright (c) 2020 CyberArk Software Ltd. All rights reserved.

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the
License. You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "
AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific
language governing permissions and limitations under the License.

For the full license text see [`LICENSE`](LICENSE).
