"""Utilities for processing and validating samples."""


def get_line(sample):
    """Build a list of relevant data to be printed.

    Args:
        sample (dict): an object from project samples

    Returns:
        list(str): list of relevant data to be printed
    """
    return "\t".join(
        [
            sample["last_status"]["created"],
            sample["id"],
            sample["client_id"],
            sample["last_status"]["status"],
            sample["archive_last_status"]["status"],
        ]
    )
