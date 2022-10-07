"""Utilities for processing pipelines."""


def get_line(pipeline):
    """Build a list of relevant data to be printed.

    Args:
        pipeline (dict): an object from project pipelines response

    Returns:
        str: tab delimited list of relevant data to be printed
    """
    return "\t".join(
        [
            str(pipeline.id),
            pipeline.version,
        ]
    )
