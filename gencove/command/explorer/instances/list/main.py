"""Configure inactivity stop for explorer instances subcommand."""

from ....base import Command
from .utils import get_line


class ListInstances(Command):
    """Configure inactivity stop for explorer instances command executor."""

    def __init__(self, hours, organization, override, credentials, options):
        super().__init__(credentials, options)
        self.hours = hours
        self.organization = organization
        self.override = override

    def initialize(self):
        """Initialize inactivity-stop subcommand."""
        self.login()

    def execute(self):
        """Make a request to list instances."""
        self.echo_debug("List instances.")

        for instance in self.api_client.get_explorer_instances().instances:
            self.echo_data(get_line(instance))
