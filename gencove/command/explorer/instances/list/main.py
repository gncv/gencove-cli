"""Configure inactivity stop for explorer instances subcommand."""

from .utils import get_line
from ....base import Command


class ListInstances(Command):
    """List explorer instances command executor."""

    def validate(self):
        """Validate list instances"""

    def initialize(self):
        """Initialize inactivity-stop subcommand."""
        self.login()

    def execute(self):
        """Make a request to list instances."""
        self.echo_debug("List instances.")

        for instance in self.api_client.get_explorer_instances().results:
            self.echo_data(get_line(instance))
