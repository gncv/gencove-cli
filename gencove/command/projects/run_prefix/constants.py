"""Constants for run-prefix command."""
from collections import namedtuple

from gencove.constants import Optionals

RunPrefixOptionals = namedtuple(
    "RunPrefixOptionals",
    Optionals._fields
    + (
        "status",
        "metadata_json",
    ),
)
