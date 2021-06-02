"""Constants for run-prefix command."""
from typing import Optional

from gencove.constants import Optionals, SampleAssignmentStatus


# pylint: disable=too-few-public-methods
class RunPrefixOptionals(Optionals):
    """RunPrefixOptionals model"""

    metadata_json: Optional[str]
    status: Optional[SampleAssignmentStatus]
