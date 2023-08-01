"""Utilities for processing projects."""
from gencove.command.utils import sanitize_string


def get_line(project, include_capability):
    """Build a list of relevant data to be printed.

    Args:
        project (Project): instance of project

    Returns:
        list(str): list of relevant data to be printed
    """
    output_list = [
        str(project.created),
        str(project.id),
        sanitize_string(project.name),
        sanitize_string(project.pipeline_capabilities.name),
    ]
    if include_capability:
        output_list.append(str(project.pipeline_capabilities.id))
        output_list.append(str(project.pipeline_capabilities.key))

    return "\t".join(output_list)
