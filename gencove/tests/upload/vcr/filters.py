"""VCR filters for upload tests."""

import copy
import json

from gencove.tests.decorators import parse_response_to_json


def filter_upload_request(request):
    """Removes destination path and aws url from request."""
    request = copy.deepcopy(request)
    if "uploads-post-data" in request.path:
        request.body = '{"destination_path": "gncv://cli-mock/test.fastq.gz"}'
    if "s3.amazonaws.com" in request.uri:
        request.uri = "https://s3.amazonaws.com/mock_bucket/organization/7d43cede-5a48-445a-91c4-e9d4f3866588/user/7d43cede-5a48-445a-91c4-e9d4f3866588/uploads/7d43cede-5a48-445a-91c4-e9d4f3866588.fastq-r1"  # noqa: E501 pylint: disable=line-too-long
    return request


@parse_response_to_json
def filter_upload_credentials_response(response, json_response):
    """Filter credentials secrets."""
    for key in ["access_key", "secret_key", "token"]:
        if key in json_response:
            json_response[key] = f"mock_{key}"
    return response, json_response


@parse_response_to_json
def filter_upload_post_data_response(response, json_response):
    """Removes sensitive data from POST to uploads-post-data."""
    mock_id = "7d43cede-5a48-445a-91c4-e9d4f3866588"
    if "id" in json_response:
        json_response["id"] = mock_id
    if "destination_path" in json_response:
        json_response["destination_path"] = "gncv://cli-mock/test.fastq.gz"
    if "s3" in json_response:
        json_response["s3"] = {
            "bucket": "mock_bucket",
            "object_name": f"organization/{mock_id}/user/{mock_id}/uploads/{mock_id}.fastq-r1",  # noqa: E501 pylint: disable=line-too-long
        }
    if "last_status" in json_response:
        json_response["last_status"]["id"] = mock_id
    return response, json_response


@parse_response_to_json
def filter_volatile_dates(response, json_response):
    """Patches volatile dates, and push them into the future, otherwise
    the app will think the token/whatever is expired.
    """
    if "expiry_time" in json_response:
        json_response["expiry_time"] = "2050-09-03T00:00:00+00:00"
    return response, json_response


def filter_aws_put(response):
    """Removes the amz id, request-id and version-id from the response."""
    for key in ["x-amz-id-2", "x-amz-request-id", "x-amz-version-id"]:
        if key in response["headers"]:
            response["headers"][key] = [f"mock_{key}"]
    return response


def _filter_sample_sheet(result):
    """Common function that filters sample sheet sensitive data."""
    mock_id = "7d43cede-5a48-445a-91c4-e9d4f3866588"
    if "client_id" in result:
        result["client_id"] = "mock_client_id"
    if "fastq" in result and "r1" in result["fastq"]:
        r1 = result["fastq"]["r1"]  # pylint: disable=invalid-name
        if "upload" in r1:
            r1["upload"] = mock_id
        if "destination_path" in r1:
            r1["destination_path"] = "gncv://cli-mock/test.fastq.gz"
        if "last_status" in r1:
            r1["last_status"]["id"] = mock_id
        if "last_status" in r1:
            r1["last_status"]["id"] = mock_id
    if "sample" in result:
        result["sample"] = mock_id


@parse_response_to_json
def filter_sample_sheet_response(response, json_response):
    """Filter sample sheet sensitive data from response."""
    if "results" in json_response:
        result = json_response["results"][0]
        _filter_sample_sheet(result)
    return response, json_response


def filter_project_samples_request(request):
    """Filter sample sheet sensitive data from request."""
    request = copy.deepcopy(request)
    if "project-samples" in request.path:
        try:
            body = json.loads(request.body)
            upload = body["uploads"][0]
            _filter_sample_sheet(upload)
            request.body = json.dumps(body).encode()
        except json.decoder.JSONDecodeError:
            pass
        # remove the project id from the url
        base_uri = request.uri.split("project-samples")[0]
        request.uri = (
            base_uri + "project-samples/7d43cede-5a48-445a-91c4-e9d4f3866588"
        )
    return request


@parse_response_to_json
def filter_project_samples_response(response, json_response):
    """Filter sample sheet sensitive data from upload response."""
    if "uploads" in json_response:
        result = json_response["uploads"][0]
        _filter_sample_sheet(result)
    return response, json_response
