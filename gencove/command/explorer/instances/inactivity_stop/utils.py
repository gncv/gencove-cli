"""Utilities for processing Explorer instances."""

from typing import Union


def hours_to_human_readable(hours: int, from_org: Union[int, None] = None) -> str:
    """Turn hours into human readable format."""
    description = "disabled" if hours == 0 else ""
    if from_org:
        if description:
            description += " applied from organization"
        else:
            description = "applied from organization"
    description = f" ({description})" if description else ""
    return f"{hours}{description}"
