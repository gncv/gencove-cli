"""Utilities for processing projects."""


def sanitize_string(output):
    """Removes unwanted characters from output string."""
    return output.replace("\t", " ")


def get_line(project):
    """Build a list of relevant data to be printed.

    Args:
        project (Project): instance of project

    Returns:
        list(str): list of relevant data to be printed
    """
    return [
        project.created,
        project.id,
        sanitize_string(project.name),
        sanitize_string(project.pipeline_capabilities.name),
    ]
