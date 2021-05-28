"""Describe all constants in Gencove CLI."""
from collections import namedtuple
from enum import Enum, unique

from gencove.models import GencoveBaseEnum

HOST = "https://api.gencove.com"


@unique
class ApiEndpoints(Enum):
    """ApiEndpoints enum"""

    GET_JWT = "/api/v2/jwt-create/"
    REFRESH_JWT = "/api/v2/jwt-refresh/"
    VERIFY_JWT = "/api/v2/jwt-verify/"
    UPLOAD_DETAILS = "/api/v2/uploads-post-data/"
    GET_UPLOAD_CREDENTIALS = "/api/v2/upload-credentials/"
    PROJECT_SAMPLES = "/api/v2/project-samples/{id}"
    SAMPLE_DETAILS = "/api/v2/samples/{id}"
    SAMPLE_QC_METRICS = "/api/v2/sample-quality-controls/{id}"
    SAMPLE_SHEET = "/api/v2/sample-sheet/"
    PROJECTS = "/api/v2/projects/"
    PIPELINE_CAPABILITES = "/api/v2/pipeline-capabilities/{id}"
    PROJECT_BATCH_TYPES = "/api/v2/project-batch-types/{id}"
    PROJECT_BATCHES = "/api/v2/project-batches/{id}"
    BATCHES = "/api/v2/batches/{id}"
    PROJECT_MERGE_VCFS = "/api/v2/project-merge-vcfs/{id}"
    SAMPLE_METADATA = "/api/v2/sample-metadata/{id}"
    PROJECT_RESTORE_SAMPLES = "/api/v2/project-restore-samples/{id}"


_SampleAssignmentStatus = namedtuple(
    "SampleAssignmentStatus", ["all", "unassigned", "assigned"]
)
SAMPLE_ASSIGNMENT_STATUS = _SampleAssignmentStatus(
    "all", "unassigned", "assigned"
)


@unique
class SampleSheetSortBy(Enum):
    """SampleSheetSortBy enum"""

    CREATED = "created"
    MODIFIED = "modified"


class SampleStatus(GencoveBaseEnum):
    """SampleStatus enum"""

    COMPLETED = "completed"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    RUNNING = "running"
    ALL = "all"


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

    CREATED = "created"
    MODIFIED = "modified"
    STATUS = "status"
    CLIENT_ID = "client_id"
    ID = "id"


@unique
class SortOrder(Enum):
    """SortOrder enum"""

    ASC = "asc"
    DESC = "desc"


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
