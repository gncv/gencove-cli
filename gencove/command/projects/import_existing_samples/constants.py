"""Constants for import-existing-samples command."""
from typing import Optional

from gencove.constants import Optionals


# pylint: disable=too-few-public-methods
class ImportExistingSamplesOptionals(Optionals):
    """ImportExistingSamplesOptionals model"""

    metadata_json: Optional[str]
