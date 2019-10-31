"""Constants for upload command."""
from collections import namedtuple

from gencove.constants import Optionals

TMP_UPLOADS_WARNING = (
    "The Gencove upload area is a temporary storage. "
    "Log into the dashboard and assign uploaded files "
    "to a project in order to avoid automatic deletion."
)

_UploadStatuses = namedtuple("UploadStatuses", ["done", "started", "failed"])
UPLOAD_STATUSES = _UploadStatuses("succeeded", "started", "failed")

FASTQ_EXTENSIONS = (".fastq.gz", ".fastq.bgz", ".fq.gz", ".fq.bgz")
UPLOAD_PREFIX = "gncv://"
UploadOptions = namedtuple(  # pylint: disable=invalid-name
    "UploadOptions", Optionals._fields + ("project_id",)
)
ASSIGN_ERROR = (
    "Your files were successfully uploaded, "
    "but there was an error automatically running them "
    "and assigning them to project id {}."
    "You can try to assign without upload using following gncv path: {}"
)
ASSIGN_BATCH_SIZE = 200
