"""Describe all constants in Gencove CLI."""
from collections import namedtuple

HOST = "https://api.gencove.com"
TMP_UPLOADS_WARNING = (
    "The Gencove upload area is a temporary storage. "
    "Log into the dashboard and assign uploaded files "
    "to a project in order to avoid automatic deletion."
)


_APIEndpoint = namedtuple(
    "ApiEndpoint",
    [
        "get_jwt",
        "refresh_jwt",
        "verify_jwt",
        "upload_details",
        "get_upload_credentials",
    ],
)
API_ENDPOINTS = _APIEndpoint(
    "/api/v2/jwt-create/",
    "/api/v2/jwt-refresh/",
    "/api/v2/jwt-verify/",
    "/api/v2/uploads-post-data/",
    "/api/v2/upload-credentials/",
)

_UploadStatuses = namedtuple("UploadStatuses", ["done", "started", "failed"])
UPLOAD_STATUSES = _UploadStatuses("succeeded", "started", "failed")


FASTQ_EXTENSIONS = (".fastq.gz", ".fastq.bgz", ".fq.gz", ".fq.bgz")
UPLOAD_PREFIX = "gncv://"
