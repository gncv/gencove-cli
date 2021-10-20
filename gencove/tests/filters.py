"""General filters for VCR cassettes."""
import copy
import re
from urllib.parse import urlparse, urlunparse

from gencove.tests.decorators import parse_response_to_json
from gencove.tests.utils import MOCK_UUID


@parse_response_to_json
def filter_jwt(respose, response_json):
    """Replace the refresh and access token with some mock up data."""
    if "refresh" in response_json and "access" in response_json:
        response_json["refresh"] = "mock_refresh"
        response_json["access"] = "mock_access"
    return respose, response_json


def replace_gencove_url_vcr(request):
    """Replace urls with 'gencove' in it."""
    request = copy.deepcopy(request)
    if "gencove" in request.uri:
        request.uri = urlunparse(
            urlparse(request.uri)._replace(netloc="www.example.com")
        )
    return request


def _replace_uuid_from_url(request, endpoint):
    """Removes the id from the last part of the URL."""
    request = copy.deepcopy(request)
    if endpoint in request.path:
        uuid = re.compile(
            r"[0-9A-F]{8}-[0-9A-F]{4}-[4][0-9A-F]{3}-[89AB][0-9A-F]{3}-[0-9A-F]{12}",  # noqa: E501 pylint: disable=line-too-long
            re.IGNORECASE,
        )
        request.uri = uuid.sub(MOCK_UUID, request.uri)
    return request


def filter_aws_headers(response):
    """Removes the amz id, request-id and version-id from the response.
    This can't be done in filter_headers.
    """
    for key in ["x-amz-id-2", "x-amz-request-id", "x-amz-version-id"]:
        if key in response["headers"]:
            response["headers"][key] = [f"mock_{key}"]
    return response


def replace_s3_from_url(request):
    """Mock the S3 URLS."""
    request = copy.deepcopy(request)
    if "s3.amazonaws.com" in request.uri:
        filename = urlparse(request.uri).path.split("/")[-1]
        request.uri = f"https://s3.amazonaws.com/{filename}"
    return request


def mock_binary_response(response):
    """Replace binary responses with a placeholder"""
    is_binary = "binary/octet-stream" in response["headers"].get(
        "Content-Type", []
    )
    if is_binary:
        response["body"]["string"] = b"""QUFBQkJC"""
        if "Content-Disposition" in response["headers"]:
            response["headers"]["Content-Disposition"] = ["attachment;"]
        if "Content-Length" in response["headers"]:
            response["headers"]["Content-Length"] = ["123"]
    return response