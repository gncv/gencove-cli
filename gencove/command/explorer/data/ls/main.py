"""Configure inactivity stop for explorer instances subcommand."""
import sys

from ..common import GencoveExplorerManager
from ....base import Command


class List(Command):
    """List Explorer contents command executor."""

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

        aws_session_credentials = self.api_client.get_explorer_data_credentials()

        explorer_manager = GencoveExplorerManager(
            aws_session_credentials=aws_session_credentials,
            user_id=self.api_client.get_user_details().id,
            organization_id=self.api_client.get_organization_details().id,
        )

        if self.path == explorer_manager.EXPLORER_SCHEME:
            for el in explorer_manager.NAMESPACE_KEYS:
                print(f"{explorer_manager.EXPLORER_SCHEME}{el}")
            sys.exit(0)
        if (
            self.path.rstrip("/")
            == f"{explorer_manager.EXPLORER_SCHEME}{explorer_manager.USERS}"
        ):
            # list_users()
            sys.exit(0)
        explorer_manager.execute_aws_s3_path("ls", self.path, self.ctx.args)

        print(explorer_manager)
