"""Constants for upload command."""
from collections import namedtuple

TMP_UPLOADS_WARNING = (
    "The Gencove upload area is a temporary storage. "
    "Log into the dashboard and assign uploaded files "
    "to a project in order to avoid automatic deletion."
)

_UploadStatuses = namedtuple("UploadStatuses", ["done", "started", "failed"])
UPLOAD_STATUSES = _UploadStatuses("succeeded", "started", "failed")

FASTQ_EXTENSIONS = (".fastq.gz", ".fastq.bgz", ".fq.gz", ".fq.bgz")
UPLOAD_PREFIX = "gncv://"
