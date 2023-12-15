"""Configure explorer data rm subcommand."""
from ..common import GencoveExplorerManager
from ....base import Command


class Remove(Command):
    """Remove Explorer contents command executor."""

    def __init__(self, ctx, path, credentials, options):
        super().__init__(credentials, options)
        self.ctx = ctx
        self.path = path

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
        explorer_manager.execute_aws_s3_path("rm", self.path, self.ctx.args)
