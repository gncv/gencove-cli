"""Constants for upload command."""

from gencove.constants import Optionals
from gencove.lib import namedtuple_dynamic

# pylint: disable=invalid-name

TMP_UPLOADS_WARNING = (
    "The Gencove upload area is a temporary storage. "
    "Log into the dashboard and assign uploaded files "
    "to a project in order to avoid automatic deletion."
)

_UploadStatuses = namedtuple_dynamic(
    "UploadStatuses", ["done", "started", "failed"]
)
UPLOAD_STATUSES = _UploadStatuses("succeeded", "started", "failed")

FASTQ_EXTENSIONS = (".fastq.gz", ".fastq.bgz", ".fq.gz", ".fq.bgz")

UploadOptions = namedtuple_dynamic(
    "UploadOptions", Optionals._fields + ("project_id", "metadata")
)

ASSIGN_ERROR = (
    "Your files were successfully uploaded, "
    "but there was an error automatically running them "
    "and assigning them to project id {}."
    "You can try to assign without upload using following gncv path: {}"
)

FastQ = namedtuple_dynamic("FastQ", ["client_id", "r_notation", "path"])

R_NOTATION_MAP = {"R1": "R1", "R2": "R2", "r1": "R1", "r2": "R2"}

_PathTemplateParts = namedtuple_dynamic(
    "PathTemplateParts", ["client_id", "r_notation"]
)
PathTemplateParts = _PathTemplateParts("client_id", "r_notation")
PATH_TEMPLATE = "{{{}}}_{{{}}}.fastq.gz".format(
    PathTemplateParts.client_id, PathTemplateParts.r_notation
)
