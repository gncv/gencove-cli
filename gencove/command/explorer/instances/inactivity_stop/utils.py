"""Utilities for processing Explorer instances."""

from typing import Union


def hours_to_human_readable(hours: Union[int, None]) -> str:
    """Turn hours into human readable format."""
    if hours == 0:
        return "0 (disabled)"
    if hours is None:
        return "None (default to organization config)"
    return str(hours)
