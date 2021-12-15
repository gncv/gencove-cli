"""Utilities for processing S3 autoimports."""


def get_line(s3_autoimport):
    """Build a list of relevant data to be printed.

    Args:
        s3_autoimport (S3ProjectImport): instance of
            S3 autoimport

    Returns:
        list(str): list of relevant data to be printed
    """
    return "\t".join(
        [
            str(s3_autoimport.id),
            str(s3_autoimport.project_id),
            str(s3_autoimport.s3_uri),
        ]
    )
