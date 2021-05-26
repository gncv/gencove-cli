"""Gencove CLI models"""
from typing import Optional
from pydantic import BaseModel  # pylint: disable=no-name-in-module


# pylint: disable=too-few-public-methods
class GencoveBaseModel(BaseModel):
    """Gencove Base Model"""

    id: Optional[str]
