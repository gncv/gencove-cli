"""Utilities for processing projects."""
from gencove.command.utils import sanitize_string


def get_line(project):
    """Build a list of relevant data to be printed.

    Args:
        project (Project): instance of project

    Returns:
        list(str): list of relevant data to be printed
    """
    return "\t".join(
        [
            project.created,
            project.id,
            sanitize_string(project.name),
            sanitize_string(project.pipeline_capabilities.name),
        ]
    )
