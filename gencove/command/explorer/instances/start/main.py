"""Configure inactivity stop for explorer instances subcommand."""

from typing import Union

from ....base import Command


class StartInstances(Command):
    """Start explorer instances command executor."""

    def initialize(self):
        """Initialize inactivity-stop subcommand."""
        self.login()

    def execute(self):
        """Make a request to configure instance stop inactivity."""
        self.echo_debug("Start explorer instances.")

        explorer_instances = self.api_client.get_explorer_instances()

        self.api_client.start_explorer_instances(
            instance_ids=[e.id for e in explorer_instances.instances]
        )
