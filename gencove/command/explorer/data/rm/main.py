"""Configure explorer data rm subcommand."""
from ..common import (
    GencoveExplorerManager,
    request_is_from_explorer,
    validate_explorer_user_data,
)
from ....base import Command
from ....utils import user_has_aws_in_path


class Remove(Command):
    """Remove Explorer contents command executor."""

    def __init__(self, ctx, path, credentials, options):
        super().__init__(credentials, options)
        self.ctx = ctx
        self.path = path

        # Populated after self.login() is called
        self.user = None
        self.organization = None
        self.aws_session_credentials = None

    def validate(self):
        """Validate rm"""
        validate_explorer_user_data(self.user, self.organization)
        user_has_aws_in_path(raise_exception=True)

    def initialize(self):
        """Initialize rm subcommand."""
        self.login()
        self.user = self.api_client.get_user_details()
        self.organization = self.api_client.get_organization_details()

        if not request_is_from_explorer():
            self.aws_session_credentials = (
                self.api_client.get_explorer_data_credentials()
            )

    def execute(self):
        """Make a request to rm Explorer objects."""
        self.echo_debug("Remove Explorer contents.")

        explorer_manager = GencoveExplorerManager(
            aws_session_credentials=self.aws_session_credentials,
            user_id=str(self.user.id),
            organization_id=str(self.organization.id),
        )
        explorer_manager.execute_aws_s3_path("rm", self.path, self.ctx.args)
