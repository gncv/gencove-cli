"""Utilities for processing batch types."""


def get_line(batch_type):
    """Build a list of relevant data to be printed.

    Args:
        batch_type (dict): an object from project batch types response

    Returns:
        str: tab delimited list of relevant data to be printed
    """
    return "\t".join(
        [
            batch_type.key,
            batch_type.description,
        ]
    )
