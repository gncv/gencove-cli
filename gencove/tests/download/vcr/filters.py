"""VCR filters for download tests."""
from gencove.tests.filters import _replace_uuid_from_url
from gencove.tests.utils import MOCK_CHECKSUM, MOCK_UUID


def filter_project_samples_request(request):
    """Filter project samples sensitive data from request."""
    return _replace_uuid_from_url(request, "project-samples")


def filter_sample_quality_controls_request(request):
    """Filter sample-quality-controls sensitive data from request."""
    return _replace_uuid_from_url(request, "sample-quality-controls")


def filter_sample_metadata_request(request):
    """Filter sample-metadata sensitive data from request."""
    return _replace_uuid_from_url(request, "sample-metadata")


def filter_files_request(request):
    """Filter file sensitive data from request."""
    return _replace_uuid_from_url(request, "files")


def filter_files_response(response):
    """Filter file sensitive data from response."""
    if ".sha256" in response["headers"].get("Content-Disposition", [""])[0]:
        filename = f"{MOCK_UUID}_R2.fastq.gz.sha256"
        response["headers"]["Content-Disposition"] = [
            f'attachment; filename="{filename}"'
        ]
        response["body"][
            "string"
        ] = f"{MOCK_CHECKSUM} *{MOCK_UUID}_R2.fastq.gz\n".encode()
    return response
