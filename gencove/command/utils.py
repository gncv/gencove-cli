"""Common utils used in multiple commands."""
import json
import uuid

import click

from gencove.logger import dump_debug_log, echo_error

map_arguments_to_human_readable = {
    "pipeline_capability_id": "Pipeline capability ID",
    "pipeline_id": "Pipeline ID",
    "project_id": "Project ID",
    "sample_ids": "sample IDs",
}


def handle_exception(message):
    """Exception handler for validation which raises an Abort"""
    echo_error(message)
    dump_debug_log()
    raise click.Abort()


def validate_uuid(ctx, param, candidate):  # pylint: disable=unused-argument
    """Test if provided string is a valid uuid version 4 string and convert
    to a hyphen uuid form if valid but no hyphens are present

    Note:
    Version 4 UUIDs have the form `xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx`
    where `x` is any hexadecimal digit and `y` is one of `8`, `9`, `a`, or `b`.

    candidate (str): uuid to check

    Returns:
        str: valid uuid v4, (8-4-4-4-12 form)

    Raises:
        Abort - if uuid is invalid.
    """
    try:
        # if version=4 attribute is set, value is silently converted
        validated_uuid = str(uuid.UUID(candidate))
    except ValueError:
        human_readable_param = map_arguments_to_human_readable.get(
            param.name, param.name
        )
        handle_exception(f"{human_readable_param} is not valid. Exiting.")
    return validated_uuid


def validate_uuid_list(ctx, param, uuids):  # pylint: disable=unused-argument
    """Test if provided sample_ids list contains only valid
    uuids when converted to a list.

    sample_ids (str): A comma separated list of uuids as a string, to check

    Returns:
        List[str]: a list of uuids

    Raises:
        Abort - if at least one uuid is invalid.
    """
    if uuids:
        try:
            uuids_list = [str(uuid.UUID(id.strip())) for id in uuids.split(",")]
        except ValueError:
            human_readable_param = map_arguments_to_human_readable.get(
                param.name, param.name
            )
            handle_exception(f"Not all {human_readable_param} are valid. Exiting.")
    return uuids_list if uuids else []


def sanitize_string(output):
    """Removes unwanted characters from output string."""
    return output.replace("\t", " ")


def is_valid_uuid(candidate):
    """Test if provided string is a valid uuid string.

    candidate (str): uuid to check

    Returns:
        bool: True if is a valid uuid, False if not
    """
    try:
        uuid.UUID(candidate)
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


def validate_file_types(candidate_file_types, valid_file_types):
    """Test if provided list of file types is valid.

    candidate_file_types (tuple of str): File types to check
    valid_file_types (list of FileType): Valid file types to check against

    Returns:
        list: [] if candidate_file_types are valid, list of invalid file types if not
    """
    file_type_keys = [file_type.key for file_type in valid_file_types]

    # file types that are in candidate_file_types but not in valid_file_types
    return list(set(candidate_file_types).difference(set(file_type_keys)))
