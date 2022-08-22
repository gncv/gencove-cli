"""VCR filters for samples tests."""
from gencove.tests.filters import _replace_uuid_from_url
from gencove.tests.utils import MOCK_CHECKSUM


def filter_samples_request(request):
    """Filter samples sensitive data from request."""
    return _replace_uuid_from_url(request, "samples")


def filter_files_response_filename(response):
    """Filter file sensitive data from response, using the same filename
    provided in the response.
    """
    if ".sha256" in response["headers"].get("Content-Disposition", [""])[0]:
        filename = response["body"]["string"].decode().split(" *")[1].strip()
        response["body"]["string"] = f"{MOCK_CHECKSUM} *{filename}\n".encode()
    return response
