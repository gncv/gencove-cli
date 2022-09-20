"""Utilities for processing file types."""


def get_line(file_type):
    """Build a list of relevant data to be printed.

    Args:
        file_type (dict): an object from file types response

    Returns:
        str: tab delimited list of relevant data to be printed.
    """
    return "\t".join(
        [
            file_type.key,
            file_type.description,
        ]
    )
