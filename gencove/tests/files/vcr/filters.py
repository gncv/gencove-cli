"""VCR filters for files tests"""
from gencove.tests.decorators import parse_response_to_json
from gencove.tests.filters import _replace_uuid_from_url


def filter_file_types_request(request):
    """Filter file types sensitive data from request."""
    return _replace_uuid_from_url(request, "file-types")


@parse_response_to_json
def filter_file_types_response(response, json_response):
    """Filter file types sensitive data from response."""
    if "results" in json_response:
        for result in json_response["results"]:
            if "key" in result:
                result["key"] = "Mock file type"
            if "description" in result and result["description"]:
                result["description"] = "Mock description"
    return response, json_response
