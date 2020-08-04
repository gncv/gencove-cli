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
        "sample_qc_metrics",
        "sample_sheet",
        "projects",
        "pipeline_capabilities",
        "project_batch_types",
        "project_batches",
        "batches",
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
    "/api/v2/sample-quality-controls/{id}",
    "/api/v2/sample-sheet/",
    "/api/v2/projects/",
    "/api/v2/pipeline-capabilities/{id}",
    "/api/v2/project-batch-types/{id}",
    "/api/v2/project-batches/{id}",
    "/api/v2/batches/{id}",
)

_SampleAssignmentStatus = namedtuple(
    "SampleAssignmentStatus", ["all", "unassigned", "assigned"]
)
SAMPLE_ASSIGNMENT_STATUS = _SampleAssignmentStatus(
    "all", "unassigned", "assigned"
)

_SampleSheetSortBy = namedtuple("SampleSheetSortBy", ["created", "modified"])
SAMPLES_SHEET_SORT_BY = _SampleSheetSortBy("created", "modified")

_SampleStatus = namedtuple(
    "SampleStatus", ["completed", "succeeded", "failed", "running", "all"]
)
SAMPLE_STATUS = _SampleStatus(
    "completed", "succeeded", "failed", "running", "all"
)

_SampleSortBy = namedtuple(
    "SampleSortFields", ["created", "modified", "status", "client_id", "id"]
)
SAMPLE_SORT_BY = _SampleSortBy(
    "created", "modified", "status", "client_id", "id"
)

_SortOrder = namedtuple("SortOrder", ["asc", "desc"])
SORT_ORDER = _SortOrder("asc", "desc")

Credentials = namedtuple("Credentials", ["email", "password", "api_key"])
Optionals = namedtuple("Optionals", ["host"])

_DownloadTemplateParts = namedtuple(
    "DownloadTemplateParts",
    [
        "client_id",
        "gencove_id",
        "file_type",
        "file_extension",
        "default_filename",
    ],
)
# pylint: disable=C0103
DownloadTemplateParts = _DownloadTemplateParts(
    "client_id",
    "gencove_id",
    "file_type",
    "file_extension",
    "default_filename",
)
DOWNLOAD_TEMPLATE = "{{{}}}/{{{}}}/{{{}}}".format(
    DownloadTemplateParts.client_id,
    DownloadTemplateParts.gencove_id,
    DownloadTemplateParts.default_filename,
)

MAX_RETRY_TIME_SECONDS = 300  # 5 minutes
FASTQ_MAP_EXTENSION = ".fastq-map.csv"
