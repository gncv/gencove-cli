"""VCR filters for samples tests."""
from gencove.tests.filters import _replace_uuid_from_url


def filter_samples_request(request):
    """Filter samples sensitive data from request."""
    return _replace_uuid_from_url(request, "samples")
