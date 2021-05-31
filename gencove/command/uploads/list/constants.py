"""Describe constants in samples subcommand."""
from typing import Optional

from gencove.constants import Optionals


# pylint: disable=too-few-public-methods
class UploadsOptions(Optionals):
    """UploadsOptions model"""

    status: Optional[str]
    search: Optional[str]
