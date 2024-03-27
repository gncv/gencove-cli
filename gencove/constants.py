"""Describe all constants in Gencove CLI."""
from enum import Enum, unique
from typing import Optional

from pydantic import BaseModel  # pylint: disable=no-name-in-module

HOST = "https://api.gencove.com"


@unique
class ApiEndpoints(Enum):
    """ApiEndpoints enum"""

    GET_JWT = "/api/v2/jwt-create/"
    REFRESH_JWT = "/api/v2/jwt-refresh/"
    UPLOAD_DETAILS = "/api/v2/uploads-post-data/"
    UPLOAD_URL = "/api/v2/uploads-url/"
    USER_DETAILS = "/api/v2/user/"
    GET_UPLOAD_CREDENTIALS = "/api/v2/upload-credentials/"
    PROJECT_SAMPLES = "/api/v2/project-samples/{id}"
    SAMPLE_DETAILS = "/api/v2/samples/{id}"
    SAMPLE_MANIFESTS = "/api/v2/sample-manifests/{id}"
    SAMPLE_QC_METRICS = "/api/v2/sample-quality-controls/{id}"
    SAMPLE_SHEET = "/api/v2/sample-sheet/"
    PROJECTS = "/api/v2/projects/"
    PIPELINE_CAPABILITES = "/api/v2/pipeline-capabilities/{id}"
    PROJECT_BATCH_TYPES = "/api/v2/project-batch-types/{id}"
    PROJECT_BATCHES = "/api/v2/project-batches/{id}"
    PROJECT_SAMPLE_MANIFESTS = "/api/v2/project-sample-manifests/{id}"
    BATCHES = "/api/v2/batches/{id}"
    PROJECT_MERGE_VCFS = "/api/v2/project-merge-vcfs/{id}"
    SAMPLE_METADATA = "/api/v2/sample-metadata/{id}"
    PROJECTS_DELETE = "/api/v2/projects-delete/"
    PROJECT_DELETE_SAMPLES = "/api/v2/project-delete-samples/{id}"
    PROJECT_RESTORE_SAMPLES = "/api/v2/project-restore-samples/{id}"
    PROJECT_QC_REPORT = "/api/v2/project-qc-report/{id}"
    BASESPACE_PROJECTS_IMPORT = "/api/v2/basespace-projects-import/"
    BASESPACE_PROJECTS_LIST = "/api/v2/basespace-projects/"
    BASESPACE_BIOSAMPLES_LIST = "/api/v2/basespace-project-biosamples/{id}"
    S3_URI_IMPORT = "/api/v2/s3-uri-import/"
    BASESPACE_PROJECTS_AUTOIMPORT = "/api/v2/basespace-projects-autoimport/"
    S3_URI_AUTOIMPORT = "/api/v2/s3-uri-autoimport/"
    FILE_CHECKSUM = "/api/v2/files/{id}.sha256"
    IMPORT_EXISTING_SAMPLES = "/api/v2/project-samples-import/"
    FILE_TYPES = "/api/v2/file-types/"
    PIPELINES = "/api/v2/pipeline/"
    PIPELINE = "/api/v2/pipeline/{id}"
    ORGANIZATION_MONTHLY_USAGE_REPORT = "/api/v2/organization-monthly-usage-report/"
    ORGANIZATION_DETAILS = "/api/v2/organization/"
    EXPLORER_INSTANCES = "/api/v2/explorer-instances/"
    EXPLORER_INSTANCES_STOP = "/api/v2/explorer-stop-instances/"
    EXPLORER_INSTANCES_START = "/api/v2/explorer-start-instances/"
    EXPLORER_INSTANCES_INACTIVITY_STOP = "/api/v2/explorer-instances-inactivity-stop/"
    EXPLORER_INSTANCES_INACTIVITY_STOP_ORGANIZATION = (
        "/api/v2/explorer-instances-inactivity-stop-organization/"
    )
    EXPLORER_SHELL_SESSION_CREDENTIALS = "/api/v2/explorer-shell-session-credentials/"
    EXPLORER_DATA_CREDENTIALS = "/api/v2/explorer-data-credentials/"


@unique
class SampleAssignmentStatus(Enum):
    """SampleAssignmentStatus enum"""

    ALL = "all"
    UNASSIGNED = "unassigned"
    ASSIGNED = "assigned"


@unique
class SampleSheetSortBy(Enum):
    """SampleSheetSortBy enum"""

    CREATED = "created"
    MODIFIED = "modified"


@unique
class SampleStatus(Enum):
    """SampleStatus enum"""

    COMPLETED = "completed"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    RUNNING = "running"
    ALL = "all"


@unique
class SampleArchiveStatus(Enum):
    """SampleArchiveStatus enum"""

    AVAILABLE = "available"
    ARCHIVED = "archived"
    RESTORE_REQUESTED = "restore_requested"
    ALL = "all"
    UNKNOWN = "unknown"


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


@unique
class PipelineSortBy(Enum):
    """PipelineSortBy enum"""

    CREATED = "created"


# pylint: disable=too-few-public-methods
class Credentials(BaseModel):
    """Credentials model"""

    email: str
    password: str
    api_key: str
    otp_token: Optional[str] = None


# pylint: disable=too-few-public-methods
class Optionals(BaseModel):
    """Optionals model"""

    host: Optional[str]


@unique
class DownloadTemplateParts(Enum):
    """DownloadTemplateParts enum"""

    CLIENT_ID = "client_id"
    GENCOVE_ID = "gencove_id"
    FILE_TYPE = "file_type"
    FILE_EXTENSION = "file_extension"
    DEFAULT_FILENAME = "default_filename"


@unique
class FileTypesObject(Enum):
    """File Type object enum"""

    SAMPLE = "sample"
    REFERENCE_GENOME = "reference_genome"


DOWNLOAD_TEMPLATE = (
    f"{{{DownloadTemplateParts.CLIENT_ID.value}}}/"
    f"{{{DownloadTemplateParts.GENCOVE_ID.value}}}/"
    f"{{{DownloadTemplateParts.DEFAULT_FILENAME.value}}}"
)

MAX_RETRY_TIME_SECONDS = 300  # 5 minutes
FASTQ_MAP_EXTENSION = ".fastq-map.csv"
UPLOAD_PREFIX = "gncv://"
ASSIGN_BATCH_SIZE = 200
IMPORT_BATCH_SIZE = 100

MINIMUM_SUPPORTED_PYTHON_MAJOR, MINIMUM_SUPPORTED_PYTHON_MINOR = 3, 8
