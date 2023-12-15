"""Configure explorer data sync subcommand."""

from ..common import GencoveExplorerManager
from ....base import Command


class Sync(Command):
    """Sync Explorer contents command executor."""

    def __init__(self, ctx, source, destination, credentials, options):
        super().__init__(credentials, options)
        self.ctx = ctx
        self.source = source
        self.destination = destination

    def validate(self):
        """Validate start instances"""

    def initialize(self):
        """Initialize inactivity-stop subcommand."""
        self.login()

    def execute(self):
        """Make a request to start explorer instances."""
        self.echo_debug("List Explorer contents.")

        explorer_manager = GencoveExplorerManager(
            aws_session_credentials=self.api_client.get_explorer_data_credentials(),
            user_id=str(self.api_client.get_user_details().id),
            organization_id=str(self.api_client.get_organization_details().id),
        )
        explorer_manager.execute_aws_s3_src_dst(
            "sync", self.source, self.destination, self.ctx.args
        )
