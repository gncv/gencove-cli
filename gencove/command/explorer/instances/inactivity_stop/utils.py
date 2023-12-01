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


def calculate_applied_hours_to_instance(instance_config, org_config):
    """Calculate applied hours to instance.

    Args:
        instance_config (dict): Instance config.
        org_config (dict): Org config.

    Returns:
        tuple(int, bool): Hours and boolean indicating if config was applied from
            org or not.
    """
    if (
        instance_config["stop_after_inactivity_hours"] is not None
        and not org_config["explorer_override_stop_after_inactivity_hours"]
    ):
        hours, from_org = instance_config["stop_after_inactivity_hours"], False
    else:
        hours, from_org = org_config["explorer_stop_after_inactivity_hours"], True
    return hours, from_org
