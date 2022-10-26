"""Utilities for processing pipeline capabilities."""


def get_line(pipeline_capability):
    """Build a list of relevant data to be printed.

    Args:
        pipeline_capability (dict): an object from pipeline capabilities response

    Returns:
        str: tab delimited list of relevant data to be printed
    """
    return "\t".join(
        [
            str(pipeline_capability.id),
            pipeline_capability.name,
            str(pipeline_capability.private),
            str(pipeline_capability.merge_vcfs_enabled),
        ]
    )
