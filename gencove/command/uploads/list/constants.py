"""Describe constants in samples subcommand."""
from typing import Optional

from gencove.constants import BaseOptionals


# pylint: disable=too-few-public-methods
class UploadsOptions(BaseOptionals):
    """UploadsOptions model"""

    status: Optional[str]
    search: Optional[str]
