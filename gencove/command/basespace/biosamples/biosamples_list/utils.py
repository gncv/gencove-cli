"""Utilities for processing BaseSpace BioSamples."""
from gencove.command.utils import sanitize_string


def get_line(biosample):
    """Build a list of relevant data to be printed.

    Args:
        biosample (BaseSpaceBioSample): instance of BaseSpaceBioSample

    Returns:
        list(str): list of relevant data to be printed
    """
    return "\t".join(
        [
            str(biosample.basespace_date_created),
            str(biosample.basespace_id),
            sanitize_string(biosample.basespace_bio_sample_name),
        ]
    )
