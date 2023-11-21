"""Configure inactivity stop for explorer instances subcommand."""

from typing import Union

from .....exceptions import ValidationError
from ....base import Command


class StopInstanceInactivity(Command):
    """Configure inactivity stop for explorer instances command executor."""

    def __init__(self, hours, organization, override, credentials, options):
        super().__init__(credentials, options)
        self.hours = hours
        self.organization = organization
        self.override = override

    def initialize(self):
        """Initialize inactivity-stop subcommand."""
        self.login()

    def validate(self):
        """Validate command input."""
        self.echo_debug("Validating instance-inactivity command input")

        self.hours_is_empty = self.hours == "placeholder"
        if self.hours in ["None", "none", "null"]:
            self.hours = None
        if not self.hours_is_empty and self.hours is not None:
            self.hours = int(self.hours)
        if not self.hours_is_empty and self.hours is not None and self.hours < 0:
            raise ValidationError("Expected 'hours' to be a positive integer or None.")
        if self.organization and self.hours is None:
            raise ValidationError(
                "Expected 'hours' to be a positive integer if '--organization' is provided."
            )
        if self.override is not None and not self.organization:
            raise ValidationError(
                "Expected '--override' to be used with '--organization' flag."
            )

    def execute(self):
        """Make a request to configure instance stop inactivity."""
        self.echo_debug("Configure explorer instances stop after inactivity.")

        instances_config, org_config = (
            self.api_client.get_explorer_instances(),
            self.api_client.get_explorer_instances_activity_stop_organization(),
        )

        request_data = {}
        if self.organization:
            if self.override is not None:
                request_data[
                    "explorer_override_stop_after_inactivity_hours"
                ] = self.override
            if not self.hours_is_empty:
                request_data["explorer_stop_after_inactivity_hours"] = self.hours
            if request_data:
                self.echo_debug("Setting configuration organization wide")
                org_config |= request_data
                self.api_client.set_explorer_instances_activity_stop_organization(
                    org_config["explorer_override_stop_after_inactivity_hours"],
                    org_config["explorer_stop_after_inactivity_hours"],
                )
        else:
            if not self.hours_is_empty:
                self.echo_debug("Setting configuration for instances")
                self.api_client.set_explorer_instances_activity_stop(
                    [e["id"] for e in instances_config], self.hours
                )
                instances_config = [
                    {"id": e["id"], "stop_after_inactivity_hours": self.hours}
                    for e in instances_config
                ]

        self.show_inactivity_config(instances_config, org_config)

    def hours_to_human_readable(self, hours: Union[int, None]) -> str:
        if hours == 0:
            return "0 (disabled)"
        if hours is None:
            return "None (default to organization config)"
        return str(hours)

    def show_inactivity_config(self, instances_config, org_config):
        self.echo_debug("Displaying inactivity config")
        self.echo_data("Inactivity stop configuration")
        self.echo_data(
            f"Organization:\t\t\t\t\thours={self.hours_to_human_readable(org_config['explorer_stop_after_inactivity_hours'])}, override={org_config['explorer_override_stop_after_inactivity_hours']}"
        )
        for instance in instances_config:
            self.echo_data(
                f"Instance {instance['id'].replace('-', '')}:\thours={self.hours_to_human_readable(instance['stop_after_inactivity_hours'])}"
            )
