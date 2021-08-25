"""Constants for s3-import command."""
from typing import Optional

from gencove.constants import Optionals


class S3ImportOptionals(Optionals):
    """S3ImportOptionals model"""

    metadata_json: Optional[str]
