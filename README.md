# {Conjur-Python-SDK}

An API client for Conjur written in python.

Find more from CyberArk.

## Certification level

{Community}
![](https://img.shields.io/badge/Certification%20Level-Community-28A745?link=https://github.com/cyberark/community/blob/master/Conjur/conventions/certification-levels.md)

This repo is a **Community** level project. It's a community contributed project that **is not reviewed or supported by
CyberArk**. For more detailed information on our certification levels,
see [our community guidelines](https://github.com/cyberark/community/blob/master/Conjur/conventions/certification-levels.md#community)
.

## Requirements

This project requires Docker and access to DockerHub.

It officially requires python3.10 and above but can run with lower versions compiled with openssl 1.1.1

TODO - add instructions to know which related to what Each python Client version corresponds to a specific API version
release,

## How to use the client

### Prerequisites

It is assumed that Conjur (OSS or Enterprise) have already been installed in the environment and running in the
background. If you haven't done so, follow these instructions for installation of
the [OSS](https://docs.conjur.org/Latest/en/Content/OSS/Installation/Install_methods.htm) and these for installation
of [Enterprise](https://docs.cyberark.com/Product-Doc/OnlineHelp/AAM-DAP/Latest/en/Content/HomeTilesLPs/LP-Tile2.htm).

Once Conjur is running in the background, you are ready to start setting up your python app to work with our Conjur
python API!

### Configuring the client

#### Define connection parameters

In order to login to conjur you need to have 5 parameters known from advance.

`conjur_url = "https://my_conjur.com"`
`account = "my_account"`
`username = "user1"`
`password = "SomeStr@ngPassword!1"`
`ssl_verification_mode = SslVerificationMode.TRUST_STORE`

#### Define ConjurrcData

ConjurrcData is a data class containing all the non-credentials connection details.
`conjurrc_data = ConjurrcData(
conjur_url=conjur_url, account=account, cert_file = None
)`

* conjur_url - url of conjur server
* account - the account which we want to connect to
* cert_file - a path to conjur rootCA file. we need it if we initialize the client in `SslVerificationMode.SELF_SIGN`
  or `SslVerificationMode.CA_BUNDLE` mode

#### Load credentials provider

The client uses credentials provider in order to get the connection credentials before making api command. This approach
allow to keep the credentials in a safe location and provide it to the client on demand.

We provide the user with `CredentialsProviderInterface` which can be implemented the way the user see as best
fit (`keyring` usage for example)

We also provide the user with a simple implementation of such provider called `SimpleCredentialsProvider`.
Example of creating such provider + storing credentials:

`credentials = CredentialsData(username=username, password=password, machine=conjur_url)`

`credentials_provider = SimpleCredentialsProvider()`

`credentials_provider.save(credentials)`

`del credentials`

#### Creating the client and use it
Now that we have created `conjurrc_data` and `credentials_provider`
We can create our client

`client = Client(conjur_data, credentials_provider=credentials_provider,
                ssl_verification_mode=ssl_verification_mode)`

* ssl_verification_mode = `SslVerificationMode` enum that states what is the certificate verification technique we will use when making the api request

After creating the client we can login to conjur and start using it. Example of usage:

`client.login() # login to conjur and return the api_key`

`client.list() # get list of all conjur resources that the user authorize to read`

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
