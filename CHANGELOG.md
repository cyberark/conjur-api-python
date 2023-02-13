# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.0.5] - 2023-02-13

### Added
- Add support for Role Memberships endpoint
  [conjur-api-python#30](https://github.com/cyberark/conjur-api-python/pull/33)
- Add support for Check Privilege endpoint
  [conjur-api-python#34](https://github.com/cyberark/conjur-api-python/pull/34)
- Add support for Show Role endpoint
  [conjur-api-python#30](https://github.com/cyberark/conjur-api-python/pull/30)
- Add `role_exists` method
  [conjur-api-python#35](https://github.com/cyberark/conjur-api-python/pull/35)
- Add support for Show Resource endpoint
  [conjur-api-python#31](https://github.com/cyberark/conjur-api-python/pull/31)
- Add `resource_exists` method
  [conjur-api-python#32](https://github.com/cyberark/conjur-api-python/pull/32)
- Add support for LDAP authentication
  [conjur-api-python#22](https://github.com/cyberark/conjur-api-python/pull/22)
- Supplying api token manually is now supported
  [conjur-api-python#19](https://github.com/cyberark/conjur-api-python/pull/19)
- Add support for OIDC authentication
  [conjur-api-python#19](https://github.com/cyberark/conjur-api-python/pull/19)
- Add support for enabling and disabling of an authenticator
  [conjur-api-python#19](https://github.com/cyberark/conjur-api-python/pull/19)
- Add support for creating hosts using host factory with provided annotations
  [conjur-api-python#19](https://github.com/cyberark/conjur-api-python/pull/19)
- The `get_server_info` method is now available in SDK. It is only supported against Conjur enterprise server
  [conjur-api-python#19](https://github.com/cyberark/conjur-api-python/pull/19)

### Changed
- Include system truststore certs even if cert_file config is present
  [conjur-api-python#37](https://github.com/cyberark/conjur-api-python/pull/37)
- Abstract authentication flow into new `AuthenticationStrategyInterface`
  [conjur-api-python#20](https://github.com/cyberark/conjur-api-python/pull/20)
- Store API key in `CreditentialsData` object
  [conjur-api-python#23](https://github.com/cyberark/conjur-api-python/pull/23)

[Unreleased]: https://github.com/cyberark/conjur-api-python/compare/v0.0.5...HEAD
[0.0.5]: https://github.com/cyberark/conjur-api-python/releases/tag/v0.0.5
