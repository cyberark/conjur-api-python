# -*- coding: utf-8 -*-

"""
SslContextFactory module
This module job is to encapsulate the creation of SSLContext in the dependent of each os environment
"""

# Builtin
import logging
import ssl
from functools import lru_cache
# nosec
import subprocess

# Internals
from conjur_api.models import SslVerificationMetadata, SslVerificationMode
from conjur_api.errors.errors import UnknownOSError, MacCertificatesError
from conjur_api.models.enums.os_types import OSTypes
from conjur_api.utils.util_functions import get_current_os

logger = logging.getLogger(__name__)

# pylint: disable=too-few-public-methods
def create_ssl_context(ssl_verification_metadata: SslVerificationMetadata) -> ssl.SSLContext:
    """
    Factory method to create SSLContext loaded with system RootCA's
    @return: SSLContext configured with the system certificates
    and/or the cert_file
    """
    os_type = get_current_os()

    if ssl_verification_metadata.mode == SslVerificationMode.TRUST_STORE:
        logger.debug("Creating SSLContext from OS TrustStore for '%s'", os_type.name)
        ssl_context = _create_ssl_context(os_type)
    else:
        ssl_context = ssl.create_default_context(cafile=ssl_verification_metadata.ca_cert_path)
        _append_system_certs(ssl_context, os_type)

    ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
    # pylint: disable=no-member
    ssl_context.verify_flags |= ssl.OP_NO_TICKET

    logger.debug("SSLContext created successfully")

    return ssl_context


def _append_system_certs(ssl_context, os_type):
    """
    Append system root CAs to the SSL context.
    """
    if os_type in (OSTypes.LINUX, OSTypes.WINDOWS):
        ssl_context.load_default_certs()
    elif os_type == OSTypes.MAC_OS:
        ssl_context.load_verify_locations(cadata=_get_mac_ca_certs())


def _create_ssl_context(os_type) -> ssl.SSLContext:
    """
    Create new SSLContext object based on the OS.
        MacOS uses the System Root keychain.
        Linux/Windows use the OpenSSL truststore.
    @return: SSLContext configured with certificates
    from the system truststore.
    """
    if os_type == OSTypes.MAC_OS:
        return ssl.create_default_context(cadata=_get_mac_ca_certs())
    if os_type in (OSTypes.LINUX, OSTypes.WINDOWS):
        return ssl.create_default_context()

    raise UnknownOSError(f"Cannot find CA certificates for OS '{os_type}'")


@lru_cache
def _get_mac_ca_certs() -> str:
    """
    Get Root CAs from Mac Keychain.
    @return: String containing trusted root CAs from the keychain.
    """
    logger.debug("Get CA certs from Mac keychain")
    try:
        get_ca_certs_process = subprocess.run(
            ["security", "find-certificate", "-a", "-p", "/System/Library/Keychains/SystemRootCertificates.keychain"],
            capture_output=True,
            timeout=10,
            check=True,
            text=True)
        return get_ca_certs_process.stdout
    except Exception as ex:
        raise MacCertificatesError() from ex
