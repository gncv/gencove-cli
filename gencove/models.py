"""Gencove CLI models"""
from enum import Enum
from uuid import UUID

from pydantic import BaseModel  # pylint: disable=no-name-in-module


# pylint: disable=too-few-public-methods
class GencoveBaseModel(BaseModel):
    """Gencove Base Model"""

    id: UUID


class GencoveBaseEnum(Enum):
    """Gencove Base Enum"""

    @classmethod
    def _asdict(cls):
        return {s.name: s.value for s in cls}
