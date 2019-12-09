"""Download command constants."""
import re
from collections import namedtuple

from gencove.constants import Optionals


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
FilePrefix = namedtuple("FilePrefix", ["dirs", "filename", "file_extension"])
FILENAME_RE = re.compile("filename=(.+)")

FILE_TYPES_MAPPER = {"fastq-r1": "fastq-r1_R1", "fastq-r2": "fastq-r2_R2"}
