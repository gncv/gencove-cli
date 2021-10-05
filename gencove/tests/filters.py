"""General filters for VCR cassettes."""
import copy
from urllib.parse import urlparse, urlunparse

from gencove.tests.decorators import parse_response_to_json
from gencove.tests.utils import MOCK_UUID


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
        base_uri = request.uri.split(endpoint)[0]
        request.uri = base_uri + f"{endpoint}/{MOCK_UUID}"
    return request
