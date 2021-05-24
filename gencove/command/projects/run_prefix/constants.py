"""Constants for run-prefix command."""

from gencove.constants import Optionals
from gencove.lib import namedtuple_dynamic

RunPrefixOptionals = namedtuple_dynamic(
    "RunPrefixOptionals",
    Optionals._fields
    + (
        "metadata_json",
        "status",
    ),
)
