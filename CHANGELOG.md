# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [8.0.0] - 2022-05-25

### Added
- The `get_server_info` method is now available in SDK. It is only supported against Conjur enterprise server
- Authentication via OIDC is now supported
- Supplying api token manually is now supported 
### Changed
- Abstract authentication flow into new `AuthenticationStrategyInterface`
  [conjur-api-python#20](https://github.com/cyberark/conjur-api-python/pull/20)
- Add support for LDAP authentication
  [conjur-api-python#22](https://github.com/cyberark/conjur-api-python/pull/22)
- Store API key in `CreditentialsData` object
  [conjur-api-python#23](https://github.com/cyberark/conjur-api-python/pull/23)


[Unreleased]: https://github.com/cyberark/conjur-api-python/compare/v8.0.0...HEAD
[8.0.0]: https://github.com/cyberark/conjur-api-python/releases/tag/v8.0.0
