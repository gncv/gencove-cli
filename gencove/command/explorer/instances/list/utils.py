"""Utilities for processing Explorer instances."""

from .....models import ExplorerInstance


def get_line(explorer_instance: ExplorerInstance):
    """Build a list of relevant data to be printed.

    Args:
        explorer_instance (ExplorerInstance): instance of
            BaseSpace autoimport

    Returns:
        list(str): list of relevant data to be printed
    """
    return "\t".join(
        [
            str(explorer_instance.id),
            str(explorer_instance.status),
        ]
    )
