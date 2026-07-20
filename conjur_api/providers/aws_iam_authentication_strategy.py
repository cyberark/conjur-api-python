# -*- coding: utf-8 -*-
"""
AWSIAMAuthenticationStrategy module

This module holds the AWSIAMAuthenticationStrategy class
"""

import json
import logging
import re
from datetime import datetime
from typing import Optional, Tuple
from urllib.parse import urlparse

import botocore.auth
import botocore.awsrequest
import botocore.credentials
import botocore.session

from conjur_api.errors.errors import MissingRequiredParameterException
from conjur_api.http.endpoints import ConjurEndpoint
from conjur_api.interface import AuthenticationStrategyInterface
from conjur_api.models.general.conjur_connection_info import ConjurConnectionInfo
from conjur_api.models.ssl.ssl_verification_metadata import SslVerificationMetadata
from conjur_api.utils import util_functions
from conjur_api.wrappers.http_wrapper import HttpVerb, invoke_endpoint

logger = logging.getLogger(__name__)

_VALID_REGION_PATTERN = re.compile(r'^[a-z]{2,3}(-[a-z]+)+-\d{1,2}$')
_STS_GLOBAL_URL = "https://sts.amazonaws.com/?Action=GetCallerIdentity&Version=2011-06-15"
_STS_REGIONAL_URL = "https://sts.{region}.amazonaws.com/?Action=GetCallerIdentity&Version=2011-06-15"
_STS_SIGNING_SERVICE = "sts"
_STS_GLOBAL_SIGNING_REGION = "us-east-1"


class AWSIAMAuthenticationStrategy(AuthenticationStrategyInterface):
    """
    AWSIAMAuthenticationStrategy

    Authenticates to Conjur using AWS IAM credentials. Signs an AWS STS
    GetCallerIdentity request with SigV4 and sends the resulting headers
    as JSON to the Conjur authn-iam endpoint.
    """

    def __init__(
        self,
        identity: str,
        service_id: str = "prod",
        aws_region: str = "us-east-1",
    ):
        """
        :param identity: Conjur host identity, e.g. "host/my-app/my-role"
        :param service_id: Conjur authn-iam service ID (default: "prod")
        :param aws_region: AWS region for STS endpoint and SigV4 signing.
                           Use "global" for the global STS endpoint (signs as us-east-1).
        """
        if not identity or not identity.strip():
            raise MissingRequiredParameterException("identity is required for authn-iam")
        if not service_id or not service_id.strip():
            raise MissingRequiredParameterException("service_id is required for authn-iam")
        if not is_valid_aws_region(aws_region):
            raise ValueError(f"Invalid AWS region: {aws_region!r}")

        self.identity = identity
        self.service_id = service_id.strip()
        self.aws_region = aws_region

    async def authenticate(
        self,
        connection_info: ConjurConnectionInfo,
        ssl_verification_data: SslVerificationMetadata,
    ) -> Tuple[str, datetime]:
        logger.debug("Authenticating to %s via authn-iam...", connection_info.conjur_url)
        headers_json = build_signed_headers(self.aws_region)
        api_token = await self._exchange_headers_for_conjur_token(
            headers_json, connection_info, ssl_verification_data
        )
        return api_token, util_functions.calculate_token_expiration(api_token)

    async def _exchange_headers_for_conjur_token(
        self,
        headers_json: str,
        connection_info: ConjurConnectionInfo,
        ssl_verification_data: SslVerificationMetadata,
    ) -> str:
        params = {
            "url": connection_info.conjur_url,
            "service_id": self.service_id,
            "account": connection_info.conjur_account,
            "login": self.identity,
        }
        response = await invoke_endpoint(
            HttpVerb.POST,
            ConjurEndpoint.AUTHENTICATE_IAM,
            params,
            headers_json,
            ssl_verification_metadata=ssl_verification_data,
            proxy_params=connection_info.proxy_params,
            headers={"Content-Type": "application/json"},
        )
        return response.text


def build_signed_headers(aws_region: str) -> str:
    """
    Sign an AWS STS GetCallerIdentity request with SigV4 and return
    the resulting headers as a JSON string for posting to Conjur.
    """
    if "global" == aws_region:
        url = _STS_GLOBAL_URL
        signing_region = _STS_GLOBAL_SIGNING_REGION
    else:
        url = _STS_REGIONAL_URL.format(region=aws_region)
        signing_region = aws_region

    host = urlparse(url).hostname
    if not is_valid_aws_host(host):
        raise ValueError(f"Invalid AWS STS endpoint host: {host!r}")

    session = botocore.session.get_session()
    raw_creds = session.get_credentials()
    if raw_creds is None:
        raise MissingRequiredParameterException(
            "No AWS credentials found — configure an instance profile, environment variables, or ~/.aws/credentials"
        )
    credentials = raw_creds.get_frozen_credentials()

    request = botocore.awsrequest.AWSRequest(method="GET", url=url, headers={"host": host})
    signer = botocore.auth.SigV4Auth(credentials, _STS_SIGNING_SERVICE, signing_region)
    signer.add_auth(request)

    signed_headers = dict(request.headers)
    return json.dumps(signed_headers)


def is_valid_aws_region(region: str) -> bool:
    if region == "global":
        return True
    return bool(_VALID_REGION_PATTERN.match(region))


def is_valid_aws_host(host: Optional[str]) -> bool:
    return host is not None and host.endswith(".amazonaws.com")
