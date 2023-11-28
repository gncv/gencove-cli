"""VCR filters for explorer tests."""
import json
from urllib.parse import urlparse

from gencove.tests.decorators import parse_response_to_json
from gencove.tests.filters import _replace_uuid_from_url
from gencove.tests.utils import MOCK_UUID


@parse_response_to_json
def filter_list_instances_response(response, json_response):
    """Filter list instances sensitive data from response."""
    if "results" in json_response:
        for result in json_response["results"]:
            if "id" in result:
                result["id"] = MOCK_UUID
    return response, json_response
