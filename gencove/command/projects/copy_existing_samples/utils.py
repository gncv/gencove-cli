"""Utilities for processing copied samples."""


def get_line(copied_sample):
    """Build a list of relevant data to be printed.

    Args:
        copied_sample (SampleCopy): instance of SampleCopy

    Returns:
        str: relevant data to be printed
    """

    return "\t".join(
        [
            str(copied_sample.sample_id),
            copied_sample.client_id if copied_sample.client_id else "",
        ]
    )
