"""Utilities for processing BaseSpace projects."""
from gencove.command.utils import sanitize_string


def get_line(basespace_project):
    """Build a list of relevant data to be printed.

    Args:
        basespace_project (BaseSpaceProject): instance of BaseSpace project

    Returns:
        list(str): list of relevant data to be printed
    """
    return "\t".join(
        [
            str(basespace_project.basespace_date_created),
            str(basespace_project.basespace_id),
            sanitize_string(basespace_project.basespace_name),
        ]
    )
