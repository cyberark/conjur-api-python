# -*- coding: utf-8 -*-

"""
Error module

This module holds Conjur SDK-specific errors for this project
"""


class CertificateHostnameMismatchException(Exception):
    """ Thrown to indicate that a mismatch in the certificate hostname. """


class BadInitializationException(Exception):
    """ Thrown to indicate object that initialized in an invalid way. """


class HttpError(Exception):
    """ Base exception for general HTTP failures """

    def __init__(self, message: str = "HTTP request failed", response: str = ""):
        self.message = message
        self.response = response
        super().__init__(self.message)


class HttpStatusError(HttpError):
    """ Exception for HTTP status failures """

    def __init__(self, status: str, message: str = "HTTP request failed", url: str = "", response: str = ""):
        self.status = status
        super().__init__(message=f"{status} ({message}) for url: {url}", response=response)


class HttpSslError(HttpError):
    """ Exception for HTTP SSL failures """

    def __init__(self, message: str = "HTTP request failed with SSL error"):
        super().__init__(message=message)


class ResourceNotFoundException(Exception):
    """ Exception when user inputted an invalid resource type """

    def __init__(self, resource: str, extra_details: str = None):
        self.message = f"Resource not found: {resource}"
        if extra_details is not None:
            self.message += f"\n{extra_details}"
        super().__init__(self.message)


class MissingRequiredParameterException(Exception):
    """ Exception for when user does not input a required parameter """

    def __init__(self, message: str = ""):
        self.message = message
        super().__init__(self.message)


class MissingApiTokenException(Exception):
    """ Exception when user tries to authenticate with token but it is missing or expired """

    def __init__(self, message: str = "API token missing or expired. Please provide a valid one."):
        self.message = message
        super().__init__(self.message)


class InvalidResourceException(Exception):
    """ Exception when user inputted an invalid resource type """

    def __init__(self, message: str = ""):
        self.message = message
        super().__init__(self.message)


class InvalidFormatException(Exception):
    """
    Exception for when user provides input that is not in the proper format
    (policy yml for example)
    """

    def __init__(self, message: str = ""):
        self.message = message
        super().__init__(self.message)


class UnknownOSError(Exception):
    """ Exception when using OS specific logic for unknown OS """

    def __init__(self, message: str = "Unknown OS"):
        self.message = message
        super().__init__(self.message)


class MacCertificatesError(Exception):
    """ Exception when failing to get root CA certificates from keychain in mac """

    def __init__(self, message: str = "Failed to get root CA certificates from keychain"):
        self.message = message
        super().__init__(self.message)


class SyncInvocationInsideEventLoopError(Exception):
    """ Exception when user is trying to run un-allowed operation """

    def __init__(self, message: str = "Client cannot be used inside event loop when initialized in sync mode"):
        self.message = message
        super().__init__(self.message)
