"""Constants for basespace-import command."""
from typing import Optional

from gencove.constants import Optionals


class BaseSpaceImportOptionals(Optionals):
    """BaseSpaceImportOptionals model"""

    metadata_json: Optional[str]
