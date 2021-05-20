"""Describe constants in samples subcommand."""
import re

from gencove.constants import Optionals, SAMPLE_ASSIGNMENT_STATUS
from gencove.lib import namedtuple_dynamic

UploadsOptions = namedtuple_dynamic(  # pylint: disable=invalid-name
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
