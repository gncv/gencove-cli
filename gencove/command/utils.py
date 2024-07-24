"""Common utils used in multiple commands."""
import json
import os
import re
import shutil
import subprocess  # nosec B404 (bandit subprocess import)
import uuid
from typing import Optional

import click

from gencove.exceptions import ValidationError  # noqa: I100
from gencove.logger import dump_debug_log, echo_error

map_arguments_to_human_readable = {
    "pipeline_capability_id": "Pipeline capability ID",
    "pipeline_id": "Pipeline ID",
    "project_id": "Project ID",
    "sample_ids": "sample IDs",
    "source_project_id": "Source project ID",
    "source_sample_ids": "source sample IDs",
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


def validate_destination_exists(
    ctx, param, candidate
):  # pylint: disable=unused-argument
    """Validate that a destination is a directory and/or exists"""
    if not os.path.exists(candidate) or not os.path.isdir(candidate):
        human_readable_param = map_arguments_to_human_readable.get(
            param.name, param.name
        )
        handle_exception(
            f"{human_readable_param} is not a directory that exists. Exiting."
        )
    return candidate


def extract_filename_from_headers(headers: dict) -> Optional[str]:
    """Extract filename from the Content-Disposition header, if present"""
    content_disposition = headers.get("content-disposition", "")
    match = re.search('filename="([^"]+)"', str(content_disposition))
    if match:
        return match.group(1)
    return None


def user_has_aws_in_path(raise_exception: bool = False) -> Optional[bool]:
    """Check if user has AWS CLI in PATH

    Args:
        raise_exception (bool): If True, will raise ValidationError if AWS CLI
            is not in PATH

    Returns:
        True if AWS CLI in PATH, False if not
    """
    if shutil.which("aws"):
        return True
    if raise_exception:
        raise ValidationError(
            "AWS CLI not available. Please follow installation instructions at "
            "https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-install.html"
        )
    return False


def user_has_supported_aws_cli(raise_exception: bool = False) -> Optional[bool]:
    """Check if installed AWS CLI version is supported.

    Args:
        raise_exception (bool): If True, will raise ValidationError if AWS CLI
            is not supported.

    Returns:
        True if AWS CLI version is supported, False if not
    """
    ssm_supported_semver = "1.16.12"
    try:
        # Disabling Bandit warnings check for execution of untrusted input and
        # starting a process with a partial path
        result = subprocess.run(  # nosec B603 B607
            ["aws", "--version"], capture_output=True, text=True, check=True
        )
        aws_version = result.stdout.split()[0]
        aws_semver = aws_version.split("/")[1].strip()
        # Required AWS CLI version that supports ssm plugin
        # https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html
        supported = aws_semver >= ssm_supported_semver
    except subprocess.CalledProcessError:
        # Handle the case where the AWS CLI is not installed or the command fails
        supported = False
    except (IndexError, AttributeError):
        # Handle unexpected output format
        supported = False
    if raise_exception and not supported:
        raise ValidationError(
            f"AWS CLI version must be >= {ssm_supported_semver}. "
            "Please follow installation instructions at "
            "https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-install.html"
        )
    return supported


def user_has_session_manager_plugin_in_path(
    raise_exception: bool = False,
) -> Optional[bool]:
    """Check if user has ssm plugin in PATH

    Args:
        raise_exception (bool): If True, will raise ValidationError if ssm plugin
            is not in PATH

    Returns:
        True if ssm plugin in PATH, False if not
    """
    if shutil.which("session-manager-plugin"):
        return True
    if raise_exception:
        raise ValidationError(
            "Session Manager plugin not available. "
            "Please follow installation instructions at "
            "https://docs.aws.amazon.com/systems-manager/latest/"
            "userguide/session-manager-working-with-install-plugin.html"
        )
    return False
