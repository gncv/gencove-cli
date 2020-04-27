"""Download command constants."""
import re
from collections import namedtuple

from gencove.constants import DownloadTemplateParts, Optionals


_SampleStatuses = namedtuple("SampleStatuses", ["succeeded", "failed"])
SAMPLE_STATUSES = _SampleStatuses("succeeded", "failed")

ALLOWED_STATUSES_RE = re.compile(
    "{}|{}".format(SAMPLE_STATUSES.succeeded, SAMPLE_STATUSES.failed),
    re.IGNORECASE,
)
KILOBYTE = 1024
MEGABYTE = 1024 * KILOBYTE
NUM_MB_IN_CHUNK = 3
CHUNK_SIZE = NUM_MB_IN_CHUNK * MEGABYTE

DownloadFilters = namedtuple(
    "Filters", ["project_id", "sample_ids", "file_types"]
)
DownloadOptions = namedtuple(  # pylint: disable=invalid-name
    "DownloadOptions",
    Optionals._fields + ("skip_existing", "download_template"),
)
DEFAULT_FILENAME_TOKEN = "{{{}}}".format(
    DownloadTemplateParts.default_filename
)
FilePrefix = namedtuple(
    "FilePrefix",
    ["dirs", "filename", "file_extension", "use_default_filename"],
)
FILENAME_RE = re.compile("filename=(.+)")

# Leaving the line below since it is a great explaination of FILE_TYPES_MAPPER
# usage:
# FILE_TYPES_MAPPER = {"fastq-r1": "fastq-r1_R1", "fastq-r2": "fastq-r2_R2"}
FILE_TYPES_MAPPER = {}

QC_FILE_TYPE = "qc"
