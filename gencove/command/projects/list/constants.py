"""Describe constants in projects subcommand."""
from typing import Optional, Union

from gencove.models import GencoveBaseModel


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
    created: Optional[str]
    organization: Optional[str]
    sample_count: Optional[int]
    pipeline_capabilities: Optional[Union[str, PipelineCapabilities]]
