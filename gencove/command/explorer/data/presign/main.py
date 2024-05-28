"""Configure explorer data presign subcommand."""
import sys

import click

from ..common import (
    GencoveExplorerManager,
    request_is_from_explorer_instance,
    validate_explorer_user_data,
)
from ....base import Command
from ....utils import user_has_aws_in_path


class Presign(Command):
    """Presign Explorer object command executor."""

    def __init__(self, ctx, path, credentials, options):
        super().__init__(credentials, options)
        self.ctx = ctx
        self.path = path

        # Populated after self.login() is called
        self.user = None
        self.organization = None
        self.aws_session_credentials = None

    def validate(self):
        """Validate presign"""
        validate_explorer_user_data(self.user, self.organization)
        user_has_aws_in_path(raise_exception=True)

    def initialize(self):
        """Initialize presign subcommand."""
        self.login()
        self.user = self.api_client.get_user_details()
        self.organization = self.api_client.get_organization_details()

        if not request_is_from_explorer_instance():
            self.aws_session_credentials = (
                self.api_client.get_explorer_data_credentials()
            )

    def execute(self):
        """Make a request to presign Explorer object."""
        self.echo_debug("Presign Explorer object.")

        explorer_manager = GencoveExplorerManager(
            aws_session_credentials=self.aws_session_credentials,
            user_id=str(self.user.id),
            organization_id=str(self.organization.id),
        )

        if self.path == explorer_manager.EXPLORER_SCHEME:
            click.echo(
                "Please provide a valid path to an Explorer object",
                err=True,
            )
            sys.exit(1)
        if (
            self.path.rstrip("/")
            == f"{explorer_manager.EXPLORER_SCHEME}{explorer_manager.USERS}"
        ):
            click.echo(
                "Please provide a valid path to an Explorer object",
                err=True,
            )
            sys.exit(1)
        explorer_manager.execute_aws_s3_path("presign", self.path, self.ctx.args)
