"""Constants for run-prefix command."""
from typing import Optional

from gencove.constants import BaseOptionals


# pylint: disable=too-few-public-methods
class RunPrefixOptionals(BaseOptionals):
    """RunPrefixOptionals model"""

    metadata_json: Optional[str]
    status: Optional[str]
