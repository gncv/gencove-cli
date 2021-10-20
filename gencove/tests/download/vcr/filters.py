"""VCR filters for download tests."""
from gencove.tests.filters import _replace_uuid_from_url


def filter_project_samples_request(request):
    """Filter project samples sensitive data from request."""
    return _replace_uuid_from_url(request, "project-samples")


def filter_sample_quality_controls_request(request):
    """Filter sample-quality-controls sensitive data from request."""
    return _replace_uuid_from_url(request, "sample-quality-controls")


def filter_sample_metadata_request(request):
    """Filter sample-metadata sensitive data from request."""
    return _replace_uuid_from_url(request, "sample-metadata")
