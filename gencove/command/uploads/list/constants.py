"""Describe constants in samples subcommand."""
from collections import namedtuple

from gencove.constants import Optionals

UploadsOptions = namedtuple(  # pylint: disable=invalid-name
    "UploadsOptions", Optionals._fields + ("status", "search")
)
