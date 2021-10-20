"""VCR filters for projects tests."""
import json
from urllib.parse import urlparse

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


def filter_post_project_restore_samples(request):
    """Filter project restore samples sensitive data from request."""
    if "project-restore-samples" in request.path:
        request = _replace_uuid_from_url(request, "project-restore-samples")
        try:
            body = json.loads(request.body)
            samples = [MOCK_UUID for _ in body["sample_ids"]]
            body["sample_ids"] = samples
            request.body = json.dumps(body).encode()
        except json.decoder.JSONDecodeError:
            pass
    return request


def filter_project_batches_request(request):
    """Filter project batches sensitive data from request."""
    if "project-batches" in request.path:
        request = _replace_uuid_from_url(request, "project-batches")
        try:
            body = json.loads(request.body)
            body["name"] = "Mock name"
            body["batch_type"] = "Mock batch_type"
            body["sample_ids"] = [MOCK_UUID for _ in body["sample_ids"]]
            request.body = json.dumps(body).encode()
        except (json.decoder.JSONDecodeError, TypeError):
            pass
    return request


@parse_response_to_json
def filter_project_batches_response(response, json_response):
    """Filter project batches sensitive data from response."""
    if "results" in json_response:
        for result in json_response["results"]:
            if "id" in result:
                result["id"] = MOCK_UUID
            if "name" in result:
                result["name"] = "Mock name"
            if "batch_type" in result:
                result["batch_type"] = "Mock batch_type"
            if "last_status" in result:
                result["last_status"]["id"] = MOCK_UUID
            for file in result.get("files", []):
                if "id" in file:
                    file["id"] = MOCK_UUID
                if "s3_path" in file:
                    file["s3_path"] = "mock/file.zip"
                if "size" in file and file["size"]:
                    file["size"] = "1"
                if "download_url" in file:
                    file["download_url"] = "https://example.com/file.zip"
    return response, json_response


def filter_batches_request(request):
    """Filter batches sensitive data from request."""
    return _replace_uuid_from_url(request, "batches")


@parse_response_to_json
def filter_batches_response(response, json_response):
    """Filter batches sensitive data from response."""
    if "id" in json_response:
        json_response["id"] = MOCK_UUID
    if "name" in json_response:
        json_response["name"] = "mock name"
    if "batch_type" in json_response:
        json_response["batch_type"] = "Mock batch_type"
    if "sample_ids" in json_response:
        json_response["sample_ids"] = [
            MOCK_UUID for _ in json_response["sample_ids"]
        ]
    if "last_status" in json_response:
        json_response["last_status"]["id"] = MOCK_UUID
    for file in json_response.get("files", []):
        if "id" in file:
            file["id"] = MOCK_UUID
        if "s3_path" in file:
            file["s3_path"] = f"mock/{file['s3_path'].split('/')[-1]}"
        if "size" in file and file["size"]:
            file["size"] = "1"
        if "download_url" in file:
            filename = urlparse(file["download_url"]).path.split("/")[-1]
            file["download_url"] = f"https://example.com/{filename}"
    return response, json_response