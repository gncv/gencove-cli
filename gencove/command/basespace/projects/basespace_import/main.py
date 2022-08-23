"""Import Biosamples from BaseSpace projects to a project subcommand."""

import json

from ....base import Command
from ....utils import is_valid_json, is_valid_uuid
from ..... import client
from .....exceptions import ValidationError


class BaseSpaceImport(Command):
    """BaseSpace import command executor."""

    def __init__(self, basespace_project_ids, project_id, credentials, options):
        super().__init__(credentials, options)
        self.basespace_project_ids = basespace_project_ids
        self.project_id = project_id
        self.metadata_json = options.metadata_json

    def initialize(self):
        """Initialize basespace-import subcommand."""
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
        """Make a request to import Biosamples from BaseSpace to a given
        project.
        """
        self.echo_debug(
            "Import Biosamples of the projects {self.basespace_project_ids} "
            f"to a project {self.project_id}"
        )

        try:
            # prepare metadata
            metadata = None
            if self.metadata_json is not None:
                metadata = json.loads(self.metadata_json)
                self.echo_info("Assigning metadata to the imported Biosamples.")
            import_basespace_projects = self.api_client.import_basespace_projects(
                basespace_project_ids=self.basespace_project_ids,
                project_id=self.project_id,
                metadata=metadata,
            )
            self.echo_debug(import_basespace_projects)
            self.echo_info("Request to import BaseSpace projects accepted.")
        except client.APIClientError:
            self.echo_error("There was an error importing Biosamples from BaseSpace.")
            raise
