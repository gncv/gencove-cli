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
            str(project.created),
            str(project.id),
            sanitize_string(project.name),
            str(project.pipeline_capabilities),
        ]
    )
