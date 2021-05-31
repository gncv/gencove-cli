"""Describe constants in samples subcommand."""
from typing import Optional

from gencove.constants import Optionals


# pylint: disable=too-few-public-methods
class SamplesOptions(Optionals):
    """SamplesOptions model"""

    status: Optional[str]
    archive_status: Optional[str]
    search: Optional[str]
