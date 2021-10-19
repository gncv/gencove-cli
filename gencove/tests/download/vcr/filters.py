"""VCR filters for download tests."""
from urllib.parse import urlparse

from gencove.tests.decorators import parse_response_to_json
from gencove.tests.filters import _replace_uuid_from_url
from gencove.tests.utils import MOCK_UUID


def filter_project_samples_request(request):
    """Filter project samples sensitive data from request."""
    return _replace_uuid_from_url(request, "project-samples")


def filter_samples_request(request):
    """Filter samples sensitive data from request."""
    return _replace_uuid_from_url(request, "samples")


def filter_sample_quality_controls_request(request):
    """Filter sample-quality-controls sensitive data from request."""
    return _replace_uuid_from_url(request, "sample-quality-controls")


def filter_sample_metadata_request(request):
    """Filter sample-metadata sensitive data from request."""
    return _replace_uuid_from_url(request, "sample-metadata")


def _filter_sample_sheet(result):
    """Common function that filters sample sheet sensitive data."""
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


@parse_response_to_json
def filter_project_samples_response(response, response_json):
    """Filter project samples sensitive data from response."""
    for result in response_json.get("results", []):
        _filter_sample_sheet(result)
    return response, response_json


@parse_response_to_json
def filter_samples_response(response, response_json):
    """Filter samples sensitive data from response."""
    _filter_sample_sheet(response_json)
    return response, response_json
