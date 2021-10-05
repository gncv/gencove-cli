"""VCR filters for projects tests."""

from gencove.tests.decorators import parse_response_to_json
from gencove.tests.filters import _replace_uuid_from_url
from gencove.tests.utils import MOCK_UUID


@parse_response_to_json
def filter_list_projects_response(response, json_response):
    """Filter list project sensitive data from response."""
    if "results" in json_response:
        for result in json_response["results"]:
            if "id" in result:
                result["id"] = MOCK_UUID
            if "name" in result:
                result["name"] = "mock name"
            if "description" in result and result["description"]:
                result["description"] = "mock description"
            if "organization" in result:
                result["organization"] = MOCK_UUID
            if "sample_count" in result:
                result["sample_count"] = 1
            if "pipeline_capabilities" in result:
                result["pipeline_capabilities"] = MOCK_UUID
            if "roles" in result:
                result["roles"]["organization"]["id"] = MOCK_UUID
            if "webhook_url" in result and result["webhook_url"]:
                result["webhook_url"] = "http://mockurl.com"
    return response, json_response


def filter_pipeline_capabilities_request(request):
    """Filter pipeline capabilities sensitive data from request."""
    return _replace_uuid_from_url(request, "pipeline-capabilities")


@parse_response_to_json
def filter_pipeline_capabilities_response(response, json_response):
    """Filter pipeline capabilities sensitive data from response."""
    if "id" in json_response:
        json_response["id"] = MOCK_UUID
    if "name" in json_response:
        json_response["name"] = "mock name"
    return response, json_response


def filter_get_project_samples_request(request):
    """Filter project samples sensitive data from request."""
    return _replace_uuid_from_url(request, "project-samples")


@parse_response_to_json
def filter_get_project_samples_response(response, json_response):
    """Filter list project samples sensitive data from response."""
    if "results" in json_response:
        for result in json_response["results"]:
            if "id" in result:
                result["id"] = MOCK_UUID
            if "client_id" in result:
                result["client_id"] = "mock client_id"
            if "physical_id" in result and result["physical_id"]:
                result["physical_id"] = "mock physical_id"
            if "legacy_id" in result and result["legacy_id"]:
                result["legacy_id"] = "mock legacy_id"
            if "last_status" in result:
                result["last_status"]["id"] = MOCK_UUID
                result["last_status"]["status"] = "mock status"
                if result["last_status"]["note"]:
                    result["last_status"]["note"] = "mock note"
            if "archive_last_status" in result:
                result["archive_last_status"]["id"] = MOCK_UUID
                result["archive_last_status"]["status"] = "mock status"
                if result["archive_last_status"]["transition_cutoff"]:
                    result["archive_last_status"][
                        "transition_cutoff"
                    ] = "mock transition_cutoff"
    return response, json_response


def filter_get_project_batch_types_request(request):
    """Filter project samples sensitive data from request."""
    return _replace_uuid_from_url(request, "project-batch-types")
