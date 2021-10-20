"""Utilities for processing BaseSpace autoimports."""


def get_line(basespace_autoimport):
    """Build a list of relevant data to be printed.

    Args:
        basespace_autoimport (BaseSpaceProjectImport): instance of
            BaseSpace autoimport

    Returns:
        list(str): list of relevant data to be printed
    """
    return "\t".join(
        [
            str(basespace_autoimport.id),
            str(basespace_autoimport.project_id),
            str(basespace_autoimport.identifier),
        ]
    )
