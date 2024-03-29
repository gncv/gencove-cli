"""Utilities for processing and validating samples."""


from gencove.constants import SampleArchiveStatus


def get_line(sample, include_run=False):
    """Build a list of relevant data to be printed.

    Args:
        sample (dict): an object from project samples

    Returns:
        list(str): list of relevant data to be printed
    """
    columns = [
        sample.last_status.created.isoformat(),
        str(sample.id),
        str(sample.client_id),
        sample.last_status.status,
        sample.archive_last_status.status
        if sample.archive_last_status is not None
        else SampleArchiveStatus.UNKNOWN.value,
    ]
    if include_run:
        columns.append(str(sample.run))

    return "\t".join(columns)
