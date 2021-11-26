"""Constants for s3-autoimport command."""
from typing import Optional

from gencove.constants import Optionals


class S3AutoImportOptionals(Optionals):
    """S3AutoImportOptionals model"""

    metadata_json: Optional[str]
