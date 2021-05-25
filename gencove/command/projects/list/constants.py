"""Describe constants in projects subcommand."""
from gencove.models import GencoveBaseModel


# pylint: disable=too-few-public-methods
class Project(GencoveBaseModel):
    """Project record"""

    name: str
    description: str
    created: str
    organization: str
    sample_count: str
    pipeline_capabilities: str


# pylint: disable=too-few-public-methods
class PipelineCapabilities(GencoveBaseModel):
    """Pipeline Capabilities record"""

    name: str
    private: str
    merge_vcfs_enabled: str


# pylint: disable=too-few-public-methods
class ProjectWithPipelineCapabilities(GencoveBaseModel):
    """Project record with PipelineCapabilities"""

    name: str
    description: str
    created: str
    organization: str
    sample_count: str
    pipeline_capabilities: PipelineCapabilities
