"""VCR filters for explorer tests."""

import json
import re

from gencove.tests.decorators import parse_response_to_json
from gencove.tests.utils import MOCK_UUID


@parse_response_to_json
def filter_list_instances_response(response, json_response):
    """Filter list instances sensitive data from response."""
    if "results" in json_response:
        for result in json_response["results"]:
            if "id" in result:
                result["id"] = MOCK_UUID
    if "instance_ids" in json_response:
        messages = []
        for msg in json_response["instance_ids"]:
            # Replace UUIDs with a MOCK_UUID string
            uuid_pattern = re.compile(
                r"\b[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89a-f][a-f0-9]{3}-[a-f0-9]{12}\b",  # noqa: E501, pylint: disable=line-too-long
                re.IGNORECASE,
            )
            messages.append(uuid_pattern.sub(MOCK_UUID, msg))
        json_response["instance_ids"] = messages

    return response, json_response


def filter_instance_ids_request(request):
    """Filter sensitive data from requests that have instance_ids."""
    if request.body is None:
        return request
    try:
        body = json.loads(request.body)
        if "instance_ids" in body:
            samples = [MOCK_UUID for _ in body["instance_ids"]]
            body["instance_ids"] = samples
            request.body = json.dumps(body).encode()
        if "instance_id" in body:
            body["instance_id"] = MOCK_UUID
            request.body = json.dumps(body).encode()
        if "id" in body:
            body["id"] = MOCK_UUID
            request.body = json.dumps(body).encode()
    except json.decoder.JSONDecodeError:
        pass
    return request


@parse_response_to_json
def filter_session_credentials_response(response, json_response):
    """Filter credentials secrets."""
    for key in [
        "access_key",
        "secret_key",
        "token",
        "ec2_instance_id",
        "ssm_document_name",
    ]:
        if key in json_response:
            json_response[key] = f"mock_{key}"
    return response, json_response


@parse_response_to_json
def filter_data_credentials_response(response, json_response):
    """Filter credentials secrets."""
    for key in ["access_key", "secret_key", "token"]:
        if key in json_response:
            json_response[key] = f"mock_{key}"
    if "id" in json_response:
        json_response["id"] = MOCK_UUID
    if "results" in json_response:
        for result in json_response["results"]:
            if "id" in result:
                result["id"] = MOCK_UUID
            if "email" in result:
                result["email"] = "email@example.com"
            if "name" in result:
                result["name"] = "mock name"
            if "roles" in result and "organization" in result["roles"]:
                role = result["roles"]["organization"]
                if "id" in role:
                    role["id"] = MOCK_UUID
    if "roles" in json_response:
        json_response["roles"]["organization"]["id"] = MOCK_UUID
    if "email" in json_response:
        json_response["email"] = "email@example.com"
    return response, json_response


@parse_response_to_json
def filter_explorer_access_url_response(response, json_response):
    """Filter url response."""
    if "url" in json_response:
        json_response[
            "url"
        ] = "https://mock-url.com/gncv-explorer/signin?access_token=123"
    return response, json_response
