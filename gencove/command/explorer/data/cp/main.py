"""Configure explorer data cp subcommand."""
from ..common import GencoveExplorerManager, validate_explorer_user_data
from ....base import Command


class Copy(Command):
    """Copy Explorer contents command executor."""

    def __init__(self, ctx, source, destination, credentials, options):
        super().__init__(credentials, options)
        self.ctx = ctx
        self.source = source
        self.destination = destination

        # Populated after self.login() is called
        self.user = None
        self.organization = None

    def validate(self):
        """Validate cp"""
        validate_explorer_user_data(self.user, self.organization)

    def initialize(self):
        """Initialize cp subcommand."""
        self.login()
        self.user = self.api_client.get_user_details()
        self.organization = self.api_client.get_organization_details()

    def execute(self):
        """Make a request to cp."""
        self.echo_debug("Copy Explorer contents.")

        explorer_manager = GencoveExplorerManager(
            aws_session_credentials=self.api_client.get_explorer_data_credentials(),
            user_id=str(self.user.id),
            organization_id=str(self.organization.id),
        )
        explorer_manager.execute_aws_s3_src_dst(
            "cp", self.source, self.destination, self.ctx.args
        )
