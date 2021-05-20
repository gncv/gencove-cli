"""Download command constants."""
import re

from gencove.constants import DownloadTemplateParts, Optionals
from gencove.lib import namedtuple_dynamic


_SampleStatuses = namedtuple_dynamic(
    "SampleStatuses", ["succeeded", "failed"]
)
_SampleArchiveStatuses = namedtuple_dynamic(
    "SampleStatuses", ["available", "restored"]
)
SAMPLE_STATUSES = _SampleStatuses("succeeded", "failed")
SAMPLE_ARCHIVE_STATUSES = _SampleArchiveStatuses("available", "restored")

ALLOWED_STATUSES_RE = re.compile(
    "{}|{}".format(SAMPLE_STATUSES.succeeded, SAMPLE_STATUSES.failed),
    re.IGNORECASE,
)
ALLOWED_ARCHIVE_STATUSES_RE = re.compile(
    "{}|{}".format(
        SAMPLE_ARCHIVE_STATUSES.available, SAMPLE_ARCHIVE_STATUSES.restored
    ),
    re.IGNORECASE,
)
KILOBYTE = 1024
MEGABYTE = 1024 * KILOBYTE
NUM_MB_IN_CHUNK = 3
CHUNK_SIZE = NUM_MB_IN_CHUNK * MEGABYTE

DownloadFilters = namedtuple_dynamic(
    "Filters", ["project_id", "sample_ids", "file_types"]
)
DownloadOptions = namedtuple_dynamic(  # pylint: disable=invalid-name
    "DownloadOptions",
    Optionals._fields + ("skip_existing", "download_template"),
)
DEFAULT_FILENAME_TOKEN = "{{{}}}".format(
    DownloadTemplateParts.default_filename
)
FilePrefix = namedtuple_dynamic(
    "FilePrefix",
    ["dirs", "filename", "file_extension", "use_default_filename"],
)
FILENAME_RE = re.compile("filename=(.+)")

# Leaving the line below since it is a great explaination of FILE_TYPES_MAPPER
# usage:
# FILE_TYPES_MAPPER = {"fastq-r1": "fastq-r1_R1", "fastq-r2": "fastq-r2_R2"}
FILE_TYPES_MAPPER = {}

QC_FILE_TYPE = "qc"
METADATA_FILE_TYPE = "metadata"
