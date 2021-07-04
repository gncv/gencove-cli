"""Common utils used in multiple commands."""
import json
import uuid


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
