"""Common utils used in multiple commands."""
import json
import uuid
import click


def validate_uuid(ctx, param, candidate: str) -> str:
    """Test if provided string is a valid uuid version 4 string.
    and convert to a hyphen uuid form if no hyphens are present

    candidate (str): uuid to check

    Returns:
        str: valid uuid v4, (8-4-4-4-12 form)
    """
    if not is_valid_uuid(candidate):
        raise click.UsageError("Project ID is not valid. Exiting.")

    return candidate if "-" in candidate else str(uuid.UUID(hex=candidate))


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
