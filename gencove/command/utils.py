"""Common utils used in multiple commands."""
import uuid

from gencove.exceptions import ValidationError


def sanitize_string(output):
    """Removes unwanted characters from output string."""
    return output.replace("\t", " ")


def validate_input(key, provided_value, allowed_values_re, allowed_values):
    """Validates provided value is in allowed values.

    Args:
        key(str): key for which the provided value is being validated
        provided_value (str): one of sort order/sort by field/sample status
        allowed_values_re(re.compiled value): values to compare against,
            compiled via re module
        allowed_values(namedtuple): of valid values for the key

    Returns:
        None: if everything is valid

    Raises:
         ValidationError: with validation error message
    """
    if not allowed_values_re.match(provided_value):
        raise ValidationError(
            "Unknown {} value: {}. Allowed values are: {}".format(
                key,
                provided_value,
                ", ".join(allowed_values._asdict().values()),
            )
        )


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
