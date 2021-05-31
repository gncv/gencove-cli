"""Describe constants in projects subcommand."""
from datetime import datetime
from typing import Optional, Union
from uuid import UUID

from pydantic import HttpUrl  # pylint: disable=no-name-in-module

from gencove.models import GencoveBaseModel  # noqa: I100


# pylint: disable=too-few-public-methods
class PipelineCapabilities(GencoveBaseModel):
    """Pipeline Capabilities record"""

    name: Optional[str]
    private: Optional[str]
    merge_vcfs_enabled: Optional[str]


# pylint: disable=too-few-public-methods
class Project(GencoveBaseModel):
    """Project record"""

    name: Optional[str]
    description: Optional[str]
    created: Optional[datetime]
    organization: Optional[str]
    sample_count: Optional[int]
    pipeline_capabilities: Optional[Union[UUID, PipelineCapabilities]]
    webhook_url: Optional[Union[HttpUrl, str]]  # deprecated
