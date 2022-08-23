"""Constants for upload command."""
from enum import Enum, unique
from typing import Optional

from pydantic import BaseModel  # pylint: disable=no-name-in-module

from gencove.constants import Optionals  # noqa: I100

# pylint: disable=invalid-name

TMP_UPLOADS_WARNING = (
    "The Gencove upload area is a temporary storage. "
    "Log into the dashboard and assign uploaded files "
    "to a project in order to avoid automatic deletion."
)


@unique
class UploadStatuses(Enum):
    """UploadStatuses enum"""

    DONE = "succeeded"
    STARTED = "started"
    FAILED = "failed"


FASTQ_EXTENSIONS = (".fastq.gz", ".fastq.bgz", ".fq.gz", ".fq.bgz")


# pylint: disable=too-few-public-methods
class UploadOptions(Optionals):
    """UploadOptions model"""

    project_id: Optional[str]
    metadata: Optional[str]


ASSIGN_ERROR = (
    "Your files were successfully uploaded, "
    "but there was an error automatically running them "
    "and assigning them to project id {}. "
    "You can try to assign without upload using following gncv path: {}"
)


# pylint: disable=too-few-public-methods
class FastQ(BaseModel):
    """FastQ model"""

    client_id: str
    r_notation: str
    path: str


R_NOTATION_MAP = {"R1": "R1", "R2": "R2", "r1": "R1", "r2": "R2"}


@unique
class PathTemplateParts(Enum):
    """PathTemplateParts enum"""

    client_id = "client_id"
    r_notation = "r_notation"


PATH_TEMPLATE = (
    f"{{{PathTemplateParts.client_id.value}}}_"
    f"{{{PathTemplateParts.r_notation.value}}}.fastq.gz"
)
