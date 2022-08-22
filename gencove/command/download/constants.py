"""Download command constants."""
import re
from enum import Enum, unique
from typing import Optional, Tuple, Union
from uuid import UUID

from pydantic import BaseModel  # pylint: disable=no-name-in-module

from gencove.constants import (  # noqa: I100
    DownloadTemplateParts,
    Optionals,
)


@unique
class SampleStatuses(Enum):
    """SampleStatuses as enum"""

    SUCCEEDED = "succeeded"
    FAILED = "failed"


@unique
class SampleArchiveStatuses(Enum):
    """SampleArchiveStatuses enum"""

    AVAILABLE = "available"
    RESTORED = "restored"


ALLOWED_STATUSES_RE = re.compile(
    f"{SampleStatuses.SUCCEEDED.value}|{SampleStatuses.FAILED.value}",
    re.IGNORECASE,
)
ALLOWED_ARCHIVE_STATUSES_RE = re.compile(
    f"{SampleArchiveStatuses.AVAILABLE.value}|{SampleArchiveStatuses.RESTORED.value}",
    re.IGNORECASE,
)
KILOBYTE = 1024
MEGABYTE = 1024 * KILOBYTE
NUM_MB_IN_CHUNK = 3
CHUNK_SIZE = NUM_MB_IN_CHUNK * MEGABYTE


# pylint: disable=too-few-public-methods
class DownloadFilters(BaseModel):
    """DownloadFilters options"""

    # project_id and sample_ids should be UUID instead of Union[UUID, str]
    # some tests break on UUID because they are using arbitrary strings
    # fix tests and then modify
    project_id: Optional[Union[UUID, str]]
    sample_ids: Optional[Tuple[Union[UUID, str], ...]]
    file_types: Optional[Tuple[str, ...]]


# pylint: disable=too-few-public-methods
class DownloadOptions(Optionals):
    """DownloadOptions model"""

    skip_existing: Optional[bool]
    download_template: Optional[str]


DEFAULT_FILENAME_TOKEN = f"{{{DownloadTemplateParts.DEFAULT_FILENAME.value}}}"


# pylint: disable=too-few-public-methods
class FilePrefix(BaseModel):
    """FilePrefix model"""

    dirs: str
    filename: str
    file_extension: str
    use_default_filename: bool


FILENAME_RE = re.compile("filename=(.+)")

# Leaving the line below since it is a great explaination of FILE_TYPES_MAPPER
# usage:
# FILE_TYPES_MAPPER = {"fastq-r1": "fastq-r1_R1", "fastq-r2": "fastq-r2_R2"}
FILE_TYPES_MAPPER = {}

QC_FILE_TYPE = "qc"
METADATA_FILE_TYPE = "metadata"
