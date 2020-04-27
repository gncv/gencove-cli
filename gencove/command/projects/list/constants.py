"""Describe constants in projects subcommand."""
from collections import namedtuple

Project = namedtuple(
    "Project",
    [
        "id",
        "name",
        "description",
        "created",
        "organization",
        "webhook_url",
        "sample_count",
        "pipeline_capabilities",
    ],
)
PipelineCapabilities = namedtuple(
    "PipelineCapabilities", ["id", "name", "private", "merge_vcfs_enabled"]
)
