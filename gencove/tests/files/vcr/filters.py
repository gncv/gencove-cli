"""VCR filters for files tests"""
from gencove.tests.filters import _replace_uuid_from_url


def filter_file_types_request(request):
    """Filter file types sensitive data from request."""
    return _replace_uuid_from_url(request, "file-types")
