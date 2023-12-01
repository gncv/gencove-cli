"""Configure inactivity stop for explorer instances subcommand."""

from .utils import calculate_applied_hours_to_instance, hours_to_human_readable
from ....base import Command
from .....exceptions import ValidationError


class StopInstanceInactivity(Command):
    """Configure inactivity stop for explorer instances command executor."""

    def __init__(  # pylint: disable=too-many-arguments
        self,
        hours,
        organization,
        override,
        credentials,
        options,
    ):
        super().__init__(credentials, options)
        self.hours = hours
        self.organization = organization
        self.override = override
        self.hours_is_empty = False

    def initialize(self):
        """Initialize inactivity-stop subcommand."""
        self.login()

    def validate(self):
        """Validate command input."""
        self.echo_debug("Validating instance-inactivity command input")

        self.hours_is_empty = self.hours is None
        if self.hours in ["None", "none", "null"]:
            self.hours = None
        if not self.hours_is_empty and self.hours is not None:
            self.hours = int(self.hours)
        if not self.hours_is_empty and self.hours is not None and self.hours < 0:
            raise ValidationError("Expected 'hours' to be a positive integer or None.")
        if self.organization and self.hours is None:
            raise ValidationError(
                "Expected 'hours' to be a positive integer if '--organization' is provided."  # noqa: E501, pylint: disable=line-too-long
            )
        if self.override is not None and not self.organization:
            raise ValidationError(
                "Expected '--override' to be used with '--organization' flag."
            )

    def execute(self):
        """Make a request to configure instance stop inactivity."""
        self.echo_debug("Configure explorer instances stop after inactivity.")

        instances_config, org_config = (
            self.api_client.get_explorer_instances().dict(),
            self.api_client.get_explorer_instances_activity_stop_organization().dict(),
        )

        if self.organization:
            self.echo_debug("Reading organization config")
            request_data = {}
            if self.override is not None:
                request_data[
                    "explorer_override_stop_after_inactivity_hours"
                ] = self.override
            if not self.hours_is_empty:
                request_data["explorer_stop_after_inactivity_hours"] = self.hours
            if request_data:
                self.echo_debug("Setting configuration organization wide")
                org_config.update(request_data)
                self.api_client.set_explorer_instances_activity_stop_organization(
                    org_config["explorer_override_stop_after_inactivity_hours"],
                    org_config["explorer_stop_after_inactivity_hours"],
                )
        else:
            self.echo_debug("Reading instances config")
            if not self.hours_is_empty:
                self.echo_debug("Setting configuration for instances")
                self.api_client.set_explorer_instances_activity_stop(
                    [e["id"] for e in instances_config["results"]], self.hours
                )
                instances_config["results"] = [
                    {"id": e["id"], "stop_after_inactivity_hours": self.hours}
                    for e in instances_config["results"]
                ]

        self.show_inactivity_config(instances_config, org_config)

    def show_inactivity_config(self, instances_config, org_config):
        """Display inactivity config"""
        self.echo_debug("Displaying inactivity config")
        self.echo_info("Inactivity stop configuration")
        if self.organization:
            org_hours = hours_to_human_readable(
                org_config["explorer_stop_after_inactivity_hours"]
            )
            org_override = org_config["explorer_override_stop_after_inactivity_hours"]
            self.echo_info(
                f"Organization:\t\t\t\t\thours={org_hours}, override={org_override}"
            )
        else:
            for instance in instances_config["results"]:
                instance_id = str(instance["id"]).replace("-", "")
                instance_hours = hours_to_human_readable(
                    instance["stop_after_inactivity_hours"]
                )
                applied_hours, from_org = calculate_applied_hours_to_instance(
                    instance, org_config
                )
                if from_org:
                    original_config = f", instance_config[hours={instance_hours}]"
                else:
                    original_config = ""
                applied_hours = hours_to_human_readable(
                    applied_hours, from_org=from_org
                )
                self.echo_info(
                    f"Instance {instance_id}:\thours={applied_hours}{original_config}"
                )
