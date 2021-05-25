"""Describe constants in projects subcommand."""
from typing import Optional

from gencove.models import GencoveBaseModel


# pylint: disable=too-few-public-methods
class Project(GencoveBaseModel):
    """Project record"""

    name: Optional[str]
    description: Optional[str]
    created: Optional[str]
    organization: Optional[str]
    sample_count: Optional[str]
    pipeline_capabilities: Optional[str]


# pylint: disable=too-few-public-methods
class PipelineCapabilities(GencoveBaseModel):
    """Pipeline Capabilities record"""

    name: Optional[str]
    private: Optional[str]
    merge_vcfs_enabled: Optional[str]


# pylint: disable=too-few-public-methods
class ProjectWithPipelineCapabilities(GencoveBaseModel):
    """Project record with PipelineCapabilities"""

    name: Optional[str]
    description: Optional[str]
    created: Optional[str]
    organization: Optional[str]
    sample_count: Optional[str]
    pipeline_capabilities: Optional[PipelineCapabilities]
