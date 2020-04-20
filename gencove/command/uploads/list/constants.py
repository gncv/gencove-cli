"""Describe constants in samples subcommand."""
import re
from collections import namedtuple

from gencove.constants import Optionals, SAMPLE_ASSIGNMENT_STATUS

UploadsOptions = namedtuple(  # pylint: disable=invalid-name
    "UploadsOptions", Optionals._fields + ("status", "search")
)

ALLOWED_STATUSES_RE = re.compile(
    "|".join(
        [
            "{}".format(status)
            for status in SAMPLE_ASSIGNMENT_STATUS._asdict().values()
        ]
    ),
    re.IGNORECASE,
)
