"""Describe constants in samples subcommand."""
import re

from gencove.constants import Optionals, SAMPLE_ARCHIVE_STATUS, SAMPLE_STATUS
from gencove.lib import namedtuple_dynamic

SamplesOptions = namedtuple_dynamic(  # pylint: disable=invalid-name
    "SamplesOptions",
    Optionals._fields + ("status", "archive_status", "search"),
)

ALLOWED_STATUSES_RE = re.compile(
    "|".join(
        ["{}".format(status) for status in SAMPLE_STATUS._asdict().values()]
    ),
    re.IGNORECASE,
)

ALLOWED_ARCHIVE_STATUSES_RE = re.compile(
    "|".join(
        [
            "{}".format(status)
            for status in SAMPLE_ARCHIVE_STATUS._asdict().values()
        ]
    ),
    re.IGNORECASE,
)
