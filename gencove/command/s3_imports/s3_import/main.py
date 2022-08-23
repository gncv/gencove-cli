"""Import samples from S3 to a project subcommand."""

import json

from ...base import Command
from ...utils import is_valid_json, is_valid_uuid
from .... import client
from ....exceptions import ValidationError


class S3Import(Command):
    """S3 import command executor."""

    def __init__(self, s3_uri, project_id, credentials, options):
        super().__init__(credentials, options)
        self.s3_uri = s3_uri
        self.project_id = project_id
        self.metadata_json = options.metadata_json

    def initialize(self):
        """Initialize s3-import subcommand."""
        self.login()

    def validate(self):
        """Validate command input.

        Raises:
            ValidationError - if something is wrong with command parameters.
        """
        if is_valid_uuid(self.project_id) is False:
            raise ValidationError("Project ID is not valid. Exiting.")
        if self.metadata_json and is_valid_json(self.metadata_json) is False:
            raise ValidationError("Metadata JSON is not valid. Exiting.")

    # no retry for timeouts in order to avoid duplicate heavy operations on
    # the backend
    def execute(self):
        """Make a request to import samples from S3 to a given
        project.
        """
        self.echo_debug(
            f"Import samples from {self.s3_uri} to project {self.project_id}"
        )

        try:
            # prepare metadata
            metadata = None
            if self.metadata_json is not None:
                metadata = json.loads(self.metadata_json)
                self.echo_info("Assigning metadata to the imported samples.")
            s3_uri_import = self.api_client.s3_uri_import(
                s3_uri=self.s3_uri,
                project_id=self.project_id,
                metadata=metadata,
            )
            self.echo_debug(s3_uri_import)
            self.echo_info("Request to import samples from S3 accepted.")
        except client.APIClientError:
            self.echo_error("There was an error importing from S3.")
            raise
