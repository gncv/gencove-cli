"""Common utils used in multiple commands."""


def sanitize_string(output):
    """Removes unwanted characters from output string."""
    return output.replace("\t", " ")
