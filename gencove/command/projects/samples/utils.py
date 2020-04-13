"""Utilities for processing and validating samples."""
from gencove.command.base import ValidationError
from gencove.command.utils import sanitize_string
from gencove.logger import echo_warning


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
        echo_warning(
            "Unknown {} value: {}. Allowed values are: {}".format(
                key,
                provided_value,
                ", ".join(allowed_values._asdict().values()),
            ),
            err=True,
        )
        raise ValidationError(
            "Unknown {} value: {}.".format(key, provided_value)
        )


def get_line(sample):
    """Build a list of relevant data to be printed.

    Args:
        sample (dict): an object from project samples

    Returns:
        list(str): list of relevant data to be printed
    """
    return [
        sample["last_status"]["created"],
        sample["id"],
        sample["client_id"],
        sample["last_status"]["status"],
    ]
