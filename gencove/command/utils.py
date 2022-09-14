"""Common utils used in multiple commands."""
import json
from typing import List
import uuid
import click

map_arguments_to_human_readable = {
    "project_id": "Project ID",
    "sample_ids": "sample IDs",
}


# pylint: disable=unused-argument
def validate_uuid(ctx, param, candidate: str) -> str:
    """Test if provided string is a valid uuid version 4 string.
    and convert to a hyphen uuid form if no hyphens are present

    candidate (str): uuid to check

    Returns:
        str: valid uuid v4, (8-4-4-4-12 form)
    """
    try:
        return str(uuid.UUID(candidate, version=4))
    except ValueError:
        human_readable_param = map_arguments_to_human_readable.get(
            param.name, param.name
        )
        raise click.UsageError(f"{human_readable_param} is not valid. Exiting.")


# pylint: disable=unused-argument
def validate_uuid_list(ctx, param, uuids: str) -> List[str]:
    """Test if provided sample_ids list contains only valid
    uuids when converted to a list.

    sample_ids (List[str]): List to check

    Returns:
        Raises a UsageError if not all are valid
    """
    if uuids:
        uuids_list = [s_id.strip() for s_id in uuids.split(",")]
        human_readable_param = map_arguments_to_human_readable.get(
            param.name, param.name
        )
        if not all(is_valid_uuid(id) for id in uuids_list):
            raise click.UsageError(
                f"Not all {human_readable_param} are valid. Exiting."
            )

    return uuids_list if uuids else []


def sanitize_string(output):
    """Removes unwanted characters from output string."""
    return output.replace("\t", " ")


def is_valid_uuid(candidate):
    """Test if provided string is a valid uuid version 4 string.

    candidate (str): uuid to check

    Returns:
        bool: True if is a valid uuid v4, False if not
    """
    try:
        uuid.UUID(candidate, version=4)
        return True
    except ValueError:
        return False


def is_valid_json(candidate):
    """Test if provided string is a valid JSON.

    candidate (str): JSON to check

    Returns:
        bool: True if is a valid JSON, False if not
    """
    try:
        json.loads(candidate)
        return True
    except ValueError:
        return False
