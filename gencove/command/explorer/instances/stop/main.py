"""Configure inactivity stop for explorer instances subcommand."""


from ....base import Command
from .....exceptions import ValidationError


class StopInstances(Command):
    """Stop explorer instances command executor."""

    def validate(self):
        """Validate stop instances"""

    def initialize(self):
        """Initialize inactivity-stop subcommand."""
        self.login()

    def execute(self):
        """Make a request to stop explorer instances."""
        self.echo_debug("Stop explorer instances.")

        explorer_instances = self.api_client.get_explorer_instances()
        self.echo_debug(f"Found {len(explorer_instances.results)} explorer instances.")

        if len(explorer_instances.results) != 1:
            raise ValidationError(
                "Command not supported. Download the latest version of the Gencove CLI."
            )

        self.api_client.stop_explorer_instances(
            instance_ids=[e.id for e in explorer_instances.results]
        )
        self.echo_debug(
            f"Requested to stop {len(explorer_instances.results)} explorer instances."
        )

        self.echo_info("Request to stop explorer instances accepted.")
