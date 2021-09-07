import copy

from gencove.tests.decorators import parse_response_to_json


def filter_upload_request(request):
    request = copy.deepcopy(request)
    if "uploads-post-data" in request.path:
        request.body = '{"destination_path": "gncv://cli-mock/test.fastq.gz"}'
    if "s3.amazonaws.com" in request.uri:
        request.uri = "https://s3.amazonaws.com/mock_bucket/organization/7d43cede-5a48-445a-91c4-e9d4f3866588/user/7d43cede-5a48-445a-91c4-e9d4f3866588/uploads/7d43cede-5a48-445a-91c4-e9d4f3866588.fastq-r1"
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
    mock_id = "7d43cede-5a48-445a-91c4-e9d4f3866588"
    if "id" in json_response:
        json_response["id"] = mock_id
    if "destination_path" in json_response:
        json_response["destination_path"] = "gncv://cli-mock/test.fastq.gz"
    if "s3" in json_response:
        json_response["s3"] = {
            "bucket": "mock_bucket",
            "object_name": f"organization/{mock_id}/user/{mock_id}/uploads/{mock_id}.fastq-r1",
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
