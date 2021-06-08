"""Utilities for processing and validating uploads from sample sheet."""


def get_line(upload):
    """Build a list of relevant data to be printed.

    Args:
        upload (dict): object from sample sheet

    Returns:
        list(str): list of relevant data to be printed
    """
    parts = [
        str(upload.client_id),
        str(upload.fastq.r1.upload),
        upload.fastq.r1.destination_path,
    ]
    if upload.fastq.r2:
        parts.append(str(upload.fastq.r2.upload))
        parts.append(upload.fastq.r2.destination_path)

    return "\t".join(parts)
