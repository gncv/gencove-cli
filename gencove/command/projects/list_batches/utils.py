"""Utilities for processing batches."""


from gencove.models import BatchDetail


def get_line(batch):
    """Build a list of relevant data to be printed.

    Args:
        batch (dict): an object from project batches response

    Returns:
        str: tab delimited list of relevant data to be printed
    """
    if isinstance(batch, BatchDetail):
        return "\t".join(
            [
                str(batch.id),
                batch.last_status.created.isoformat(),
                batch.last_status.status,
                batch.batch_type,
                batch.name,
            ]  # noqa
        )
    else:
        return "\t".join(
            [
                batch["id"],
                batch["last_status"]["created"],
                batch["last_status"]["status"],
                batch["batch_type"],
                batch["name"],
            ]  # noqa
        )
