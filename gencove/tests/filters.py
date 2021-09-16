"""General filters for VCR cassettes."""
import copy
from urllib.parse import urlparse, urlunparse

from gencove.tests.decorators import parse_response_to_json


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
