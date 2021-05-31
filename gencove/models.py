"""Gencove CLI models"""
from uuid import UUID

from pydantic import BaseModel  # pylint: disable=no-name-in-module


# pylint: disable=too-few-public-methods
class GencoveBaseModel(BaseModel):
    """Gencove Base Model"""

    id: UUID


class RefreshJWTResponse(BaseModel):
    access: str
