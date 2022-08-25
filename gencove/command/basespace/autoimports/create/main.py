"""AutoImport Biosamples from BaseSpace projects to a project subcommand."""

import json

from ....base import Command
from ....utils import is_valid_json, is_valid_uuid
from ..... import client
from .....exceptions import ValidationError


class BaseSpaceAutoImport(Command):
    """BaseSpace autoimport command executor."""

    def __init__(self, project_id, identifier, credentials, options):
        super().__init__(credentials, options)
        self.project_id = project_id
        self.identifier = identifier
        self.metadata_json = options.metadata_json

    def initialize(self):
        """Initialize basespace-autoimport subcommand."""
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
        """Make a request to create a job to periodically import Biosamples
        from BaseSpace projects whose name contain the identifier to a
        Gencove project.
        """
        self.echo_debug(
            "Create AutoImport job of the "
            f"identifier {self.identifier} to a project {self.project_id}"
        )

        try:
            # prepare metadata
            metadata = None

            if self.metadata_json is not None:
                metadata = json.loads(self.metadata_json)
                self.echo_info("Metadata will be assigned to the imported Biosamples.")
            autoimport_from_basespace = self.api_client.autoimport_from_basespace(
                project_id=self.project_id,
                identifier=self.identifier,
                metadata=metadata,
            )

            self.echo_debug(autoimport_from_basespace)
            action = autoimport_from_basespace["action"]
            self.echo_info(
                f"Request to {action} a periodic import job of BaseSpace "
                "projects accepted."
            )
        except client.APIClientError:
            self.echo_error(
                "There was an error creating a periodic import job of "
                "BaseSpace projects."
            )
            raise
