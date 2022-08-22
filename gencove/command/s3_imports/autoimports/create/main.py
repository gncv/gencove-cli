"""AutoImport S3 URI to a project subcommand."""

import json

from ..... import client
from .....exceptions import ValidationError
from ....base import Command  # noqa: I100
from ....utils import is_valid_json, is_valid_uuid


class S3AutoImport(Command):
    """S3AutoImport autoimport command executor."""

    def __init__(self, project_id, s3_uri, credentials, options):
        super().__init__(credentials, options)
        self.project_id = project_id
        self.s3_uri = s3_uri
        self.metadata_json = options.metadata_json

    def initialize(self):
        """Initialize s3-autoimport subcommand."""
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
        """Make a request to create a job to automatically import
        from S3 URI to a Gencove project.
        """
        self.echo_debug(
            "Create AutoImport job from "
            f"s3_uri {self.s3_uri} to project {self.project_id}"
        )

        try:
            # prepare metadata
            metadata = None
            if self.metadata_json is not None:
                metadata = json.loads(self.metadata_json)
                self.echo_info("Metadata will be assigned to the imported Biosamples.")
            autoimport_from_s3 = self.api_client.autoimport_from_s3(
                project_id=self.project_id,
                s3_uri=self.s3_uri,
                metadata=metadata,
            )
            self.echo_info(
                "Request to create a periodic import job from"
                "S3 URI to project accepted."
            )
            self.echo_data(
                "\t".join(
                    [
                        str(autoimport_from_s3.id),
                        autoimport_from_s3.topic_arn,
                    ]
                )
            )
        except client.APIClientError:
            self.echo_error("There was an error creating an import job of S3 URI.")
            raise
