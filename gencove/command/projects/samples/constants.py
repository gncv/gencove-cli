"""Describe constants in samples subcommand."""
from collections import namedtuple

from gencove.constants import Optionals

SamplesOptions = namedtuple(  # pylint: disable=invalid-name
    "SamplesOptions",
    Optionals._fields + ("status", "archive_status", "search"),
)
