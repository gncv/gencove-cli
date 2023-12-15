"""Configure explorer data rm subcommand."""
from gencove.exceptions import ValidationError
from ..common import GencoveExplorerManager
from ....base import Command


class Remove(Command):
    """Remove Explorer contents command executor."""

    def __init__(self, ctx, path, credentials, options):
        super().__init__(credentials, options)
        self.ctx = ctx
        self.path = path

        # Populated after self.login() is called
        self.user = None
        self.organization = None

    def validate(self):
        """Validate rm"""
        if not self.user.explorer_enabled:
            raise ValidationError(
                "Explorer is not enabled on your user account, quitting. "
                "Please reach out to your organization owner to inquire about Gencove Explorer."
            )

        if not self.user or not self.organization:
            raise ValidationError("Could not retrieve user details, quitting.")

    def initialize(self):
        """Initialize rm subcommand."""
        self.login()
        self.user = self.api_client.get_user_details()
        self.organization = self.api_client.get_organization_details()

    def execute(self):
        """Make a request to rm Explorer objects."""
        self.echo_debug("Remove Explorer contents.")

        explorer_manager = GencoveExplorerManager(
            aws_session_credentials=self.api_client.get_explorer_data_credentials(),
            user_id=str(self.user.id),
            organization_id=str(self.organization.id),
        )
        explorer_manager.execute_aws_s3_path("rm", self.path, self.ctx.args)
