import json

from gencove.tests.filters import _replace_uuid_from_url
from gencove.tests.utils import MOCK_UUID


def filter_get_sample_manifest_response(response):
    if response["status"]["code"] == 404:
        return response
    try:
        body = json.loads(response["body"]["string"])
        body["id"] = MOCK_UUID
        body["file_name"] = "example.csv"
        body["file"] = {
            "id": MOCK_UUID,
            "s3_path": "s3://example/example.csv",
            "size": 100,
            "download_url": "https://example.com/example.csv",
            "file_type": "sample_manifest-csv",
            "checksum_256": "",
        }
        body["project"] = MOCK_UUID
        body["created"] = "2023-08-28T14:50:34.455552Z"
        response["body"]["string"] = json.dumps(body).encode()
    except json.decoder.JSONDecodeError:
        pass
    return response


def filter_sample_manifest_request(request):
    """Filter project UUID data from request."""
    return _replace_uuid_from_url(request, "sample-manifests")
