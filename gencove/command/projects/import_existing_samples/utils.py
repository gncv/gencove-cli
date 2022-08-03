"""Utilities for processing imported samples."""


def get_line(imported_sample):
    """Build a list of relevant data to be printed.

    Args:
        imported_sample (SampleImport): instance of SampleImport

    Returns:
        str: relevant data to be printed
    """

    return "\t".join(
        [
            str(imported_sample.sample_id),
            imported_sample.client_id if imported_sample.client_id else "",
        ]
    )


def is_valid_client_id(candidate):
    """Test if provided string is a valid client id.

    candidate (str): client id to check

    Returns:
        bool: True if is a valid client id, False if not
    """
    return "_" not in candidate
