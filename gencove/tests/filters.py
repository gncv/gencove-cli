"""General filters for VCR cassettes."""
import copy
import re
from urllib.parse import urlparse, urlunparse

from gencove.tests.decorators import parse_response_to_json
from gencove.tests.utils import MOCK_CHECKSUM, MOCK_UUID


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
    is_binary = "binary/octet-stream" in response["headers"].get("Content-Type", [])
    if is_binary:
        response["body"]["string"] = b"""QUFBQkJC"""
        if "Content-Disposition" in response["headers"]:
            response["headers"]["Content-Disposition"] = ["attachment;"]
        if "Content-Length" in response["headers"]:
            response["headers"]["Content-Length"] = ["123"]
    return response


def filter_samples_request(request):
    """Filter samples sensitive data from request."""
    return _replace_uuid_from_url(request, "samples")


def _filter_sample(result):
    """Common function that filters sample sensitive data."""
    # pylint: disable=too-many-branches
    if "id" in result:
        result["id"] = MOCK_UUID
    if "client_id" in result:
        result["client_id"] = "mock_client_id"
    if "project" in result:
        result["project"] = MOCK_UUID
    if "physical_id" in result and result["physical_id"]:
        result["physical_id"] = "mock_physical_id"
    if "legacy_id" in result and result["legacy_id"]:
        result["legacy_id"] = "mock_legacy_id"
    if "last_status" in result:
        result["last_status"]["id"] = MOCK_UUID
    if "archive_last_status" in result:
        result["archive_last_status"]["id"] = MOCK_UUID
    for file in result.get("files", []):
        if "id" in file:
            file["id"] = MOCK_UUID
        if "s3_path" in file:
            file["s3_path"] = f"mock/{file['s3_path'].split('/')[-1]}"
        if "size" in file and file["size"]:
            file["size"] = "1"
        if "download_url" in file and file["download_url"]:
            filename = urlparse(file["download_url"]).path.split("/")[-1]
            file["download_url"] = f"https://example.com/{filename}"
        if "checksum_sha256" in file and file["checksum_sha256"]:
            file["checksum_sha256"] = MOCK_CHECKSUM


@parse_response_to_json
def filter_project_samples_response(response, response_json):
    """Filter project samples sensitive data from response."""
    for result in response_json.get("results", []):
        _filter_sample(result)
    return response, response_json


@parse_response_to_json
def filter_samples_response(response, response_json):
    """Filter samples sensitive data from response."""
    _filter_sample(response_json)
    return response, response_json


def filter_file_types_request(request):
    """Filter file types sensitive data from request."""
    return _replace_uuid_from_url(request, "file-types")
