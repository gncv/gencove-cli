"""Configure explorer data sync subcommand."""
import os
import uuid

from ..common import (
    GencoveExplorerManager,
    request_is_from_explorer,
    validate_explorer_user_data,
)
from ....base import Command
from ....utils import user_has_aws_in_path


class Sync(Command):
    """Sync Explorer contents command executor."""

    def __init__(self, ctx, source, destination, credentials, options):
        super().__init__(credentials, options)
        self.ctx = ctx
        self.source = source
        self.destination = destination

        # Populated after self.login() is called
        self.user_id = None
        self.organization_id = None
        self.aws_session_credentials = None

        # populated after self.execute() is called
        self.organization_users = None

    def validate(self):
        """Validate sync"""
        validate_explorer_user_data(self.user, self.organization)
        user_has_aws_in_path(raise_exception=True)

    def initialize(self):
        """Initialize sync subcommand."""
        self.login()

        if not request_is_from_explorer():
            self.user_id = self.api_client.get_user_details().id
            self.organization_id = self.api_client.get_organization_details().id
            self.aws_session_credentials = (
                self.api_client.get_explorer_data_credentials()
            )
        else:
            self.user_id = uuid.UUID(os.getenv("GENCOVE_USER_ID"))
            self.organization_id = uuid.UUID(os.getenv("GENCOVE_ORGANIZATION_ID"))

    def execute(self):
        """Make a request to sync Explorer objects."""
        self.echo_debug("Sync Explorer contents.")

        explorer_manager = GencoveExplorerManager(
            aws_session_credentials=self.aws_session_credentials,
            user_id=str(self.user_id),
            organization_id=str(self.organization_id),
            organization_users=self.api_client.get_organization_users(),
        )
        explorer_manager.execute_aws_s3_src_dst(
            "sync", self.source, self.destination, self.ctx.args
        )
