"""Describe constants in samples subcommand."""
from gencove.constants import Optionals
from gencove.lib import namedtuple_dynamic


UploadsOptions = namedtuple_dynamic(  # pylint: disable=invalid-name
    "UploadsOptions", Optionals._fields + ("status", "search")
)
