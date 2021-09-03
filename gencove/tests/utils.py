import copy
from urllib.parse import urlunparse, urlparse


def replace_gencove_url_vcr(request):
    """Replace urls with 'genconve' in it."""
    request = copy.deepcopy(request)
    if "gencove" in request.uri:
        request.uri = urlunparse(
            urlparse(request.uri)._replace(netloc="www.example.com")
        )
    return request
