"""Describe constants in samples subcommand."""
from typing import Optional

from gencove.constants import Optionals


# pylint: disable=too-few-public-methods
class SamplesOptions(Optionals):
    """SamplesOptions model"""

    status: Optional[str] = None
    archive_status: Optional[str] = None
    search: Optional[str] = None
    include_run: Optional[bool] = None
    include_hidden: Optional[bool] = None
