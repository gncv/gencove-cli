"""Describe constants in samples subcommand."""
import re
from collections import namedtuple

from gencove.constants import (
    Optionals,
    SORT_ORDER,
    SAMPLE_STATUS,
    SAMPLE_SORT_BY,
)

SamplesOptions = namedtuple(  # pylint: disable=invalid-name
    "SamplesOptions",
    Optionals._fields
    + ("status", "search", "sort_by", "sort_order", "limit"),
)

ALLOWED_STATUSES_RE = re.compile(
    "|".join(
        ["{}".format(status) for status in SAMPLE_STATUS._asdict().values()]
    ),
    re.IGNORECASE,
)

ALLOWED_SORT_FIELDS_RE = re.compile(
    "|".join(
        [
            "{}".format(sort_by)
            for sort_by in SAMPLE_SORT_BY._asdict().values()
        ]
    ),
    re.IGNORECASE,
)

ALLOWED_SORT_ORDER_RE = re.compile(
    "{}|{}".format(SORT_ORDER.asc, SORT_ORDER.desc), re.IGNORECASE
)
