"""Describe constants in projects subcommand."""
from collections import namedtuple

ProjectBase = namedtuple(
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


class Project(ProjectBase):
    """Project record"""

    __slots__ = ()

    def __new__(cls, *args, **kwargs):
        for key in tuple(kwargs):
            if key not in cls._fields:
                del kwargs[key]
        return super().__new__(cls, *args, **kwargs)


PipelineCapabilities = namedtuple(
    "PipelineCapabilities", ["id", "name", "private", "merge_vcfs_enabled"]
)
