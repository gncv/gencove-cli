"""Describe constants in projects subcommand."""
from gencove.lib import namedtuple_dynamic

Project = namedtuple_dynamic(
    "Project",
    [
        "id",
        "name",
        "description",
        "created",
        "organization",
        "sample_count",
        "pipeline_capabilities",
    ],
)

PipelineCapabilities = namedtuple_dynamic(
    "PipelineCapabilities", ["id", "name", "private", "merge_vcfs_enabled"]
)
