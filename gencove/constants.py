"""Describe all constants in Gencove CLI."""
from collections import namedtuple

HOST = "https://api.gencove.com"

_APIEndpoint = namedtuple(
    "ApiEndpoint",
    [
        "get_jwt",
        "refresh_jwt",
        "verify_jwt",
        "upload_details",
        "get_upload_credentials",
        "project_samples",
        "sample_details",
        "sample_sheet",
    ],
)
API_ENDPOINTS = _APIEndpoint(
    "/api/v2/jwt-create/",
    "/api/v2/jwt-refresh/",
    "/api/v2/jwt-verify/",
    "/api/v2/uploads-post-data/",
    "/api/v2/upload-credentials/",
    "/api/v2/project-samples/{id}",
    "/api/v2/samples/{id}",
    "/api/v2/sample-sheet/",
)

_SampleStatuses = namedtuple("SampleStatuses", ["succeeded", "failed"])
SAMPLE_STATUSES = _SampleStatuses("succeeded", "failed")

_SampleAssignmentStatus = namedtuple(
    "SampleAssignmentStatus", ["all", "unassigned", "assigned"]
)
SAMPLE_ASSIGNMENT_STATUS = _SampleAssignmentStatus(
    "all", "unassigned", "assigned"
)

Credentials = namedtuple("Credentials", ["email", "password"])
Optionals = namedtuple("Optionals", ["host"])

_DownloadTemplateParts = namedtuple(
    "DownloadTemplateParts", ["client_id", "gencove_id"]
)
DownloadTemplateParts = _DownloadTemplateParts("client_id", "gencove_id")
DOWNLOAD_TEMPLATE = "{{{}}}/{{{}}}/{{{}}}_".format(
    DownloadTemplateParts.client_id,
    DownloadTemplateParts.gencove_id,
    DownloadTemplateParts.gencove_id,
)
