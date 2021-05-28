"""Describe all constants in Gencove CLI."""
from collections import namedtuple
from enum import Enum, unique

HOST = "https://api.gencove.com"


@unique
class ApiEndpoints(Enum):
    """ApiEndpoints enum"""

    get_jwt = "/api/v2/jwt-create/"
    refresh_jwt = "/api/v2/jwt-refresh/"
    verify_jwt = "/api/v2/jwt-verify/"
    upload_details = "/api/v2/uploads-post-data/"
    get_upload_credentials = "/api/v2/upload-credentials/"
    project_samples = "/api/v2/project-samples/{id}"
    sample_details = "/api/v2/samples/{id}"
    sample_qc_metrics = "/api/v2/sample-quality-controls/{id}"
    sample_sheet = "/api/v2/sample-sheet/"
    projects = "/api/v2/projects/"
    pipeline_capabilities = "/api/v2/pipeline-capabilities/{id}"
    project_batch_types = "/api/v2/project-batch-types/{id}"
    project_batches = "/api/v2/project-batches/{id}"
    batches = "/api/v2/batches/{id}"
    project_merge_vcfs = "/api/v2/project-merge-vcfs/{id}"
    sample_metadata = "/api/v2/sample-metadata/{id}"
    project_restore_samples = "/api/v2/project-restore-samples/{id}"


_SampleAssignmentStatus = namedtuple(
    "SampleAssignmentStatus", ["all", "unassigned", "assigned"]
)
SAMPLE_ASSIGNMENT_STATUS = _SampleAssignmentStatus(
    "all", "unassigned", "assigned"
)


@unique
class SampleSheetSortBy(Enum):
    """SampleSheetSortBy enum"""

    created = "created"
    modified = "modified"


_SampleStatus = namedtuple(
    "SampleStatus", ["completed", "succeeded", "failed", "running", "all"]
)
SAMPLE_STATUS = _SampleStatus(
    "completed", "succeeded", "failed", "running", "all"
)

_SampleArchiveStatus = namedtuple(
    "SampleArchiveStatus",
    [
        "available",
        "archived",
        "restore_requested",
        "all",
    ],
)

SAMPLE_ARCHIVE_STATUS = _SampleArchiveStatus(
    "available",
    "archived",
    "restore_requested",
    "all",
)


@unique
class SampleSortBy(Enum):
    """SampleSortBy enum"""

    created = "created"
    modified = "modified"
    status = "status"
    client_id = "client_id"
    id = "id"


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
UPLOAD_PREFIX = "gncv://"
ASSIGN_BATCH_SIZE = 200
