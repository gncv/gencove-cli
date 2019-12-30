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

_SampleAssignmentStatus = namedtuple(
    "SampleAssignmentStatus", ["all", "unassigned", "assigned"]
)
SAMPLE_ASSIGNMENT_STATUS = _SampleAssignmentStatus(
    "all", "unassigned", "assigned"
)

Credentials = namedtuple("Credentials", ["email", "password", "api_key"])
Optionals = namedtuple("Optionals", ["host"])

_DownloadTemplateParts = namedtuple(
    "DownloadTemplateParts",
    ["client_id", "gencove_id", "file_type", "file_extension"],
)
# pylint: disable=C0103
DownloadTemplateParts = _DownloadTemplateParts(
    "client_id", "gencove_id", "file_type", "file_extension"
)
DOWNLOAD_TEMPLATE = "{{{}}}/{{{}}}/{{{}}}_{{{}}}.{{{}}}".format(
    DownloadTemplateParts.client_id,
    DownloadTemplateParts.gencove_id,
    DownloadTemplateParts.gencove_id,
    DownloadTemplateParts.file_type,
    DownloadTemplateParts.file_extension,
)

MAX_RETRY_TIME_SECONDS = 300  # 5 minutes
FASTQ_MAP_EXTENSION = ".fastq-map.csv"
