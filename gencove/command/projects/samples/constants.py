"""Describe constants in samples subcommand."""
from gencove.constants import Optionals
from gencove.lib import namedtuple_dynamic


SamplesOptions = namedtuple_dynamic(  # pylint: disable=invalid-name
    "SamplesOptions",
    Optionals._fields + ("status", "archive_status", "search"),
)
