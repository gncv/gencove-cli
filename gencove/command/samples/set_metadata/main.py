"""Set sample metadata subcommand."""

import json

from ...base import Command
from ...utils import is_valid_uuid
from .... import client
from ....exceptions import ValidationError


class SetMetadata(Command):
    """Set metadata command executor."""

    def __init__(self, sample_id, json_metadata, credentials, options):
        super().__init__(credentials, options)
        self.sample_id = sample_id
        self.json_metadata = json_metadata

    def initialize(self):
        """Initialize set-metadata subcommand."""
        self.login()

    def validate(self):
        """Validate command input.

        Raises:
            ValidationError - if something is wrong with command parameters.
        """

        if is_valid_uuid(self.sample_id) is False:
            raise ValidationError("Sample ID is not valid. Exiting.")

        if self._valid_json(self.json_metadata) is False:
            raise ValidationError("Metadata JSON is not valid. Exiting.")

    # no retry for timeouts in order to avoid duplicate heavy operations on
    # the backend
    def execute(self):
        """Make a request to assign given metadata to a specified sample."""

        self.echo_debug(
            "Assigning metadata to a sample {}".format(self.sample_id)
        )

        try:
            metadata_api = None
            if self.json_metadata is not None:
                metadata_api = json.loads(self.json_metadata)
            assigned_metadata = self.api_client.set_metadata(
                self.sample_id, metadata_api
            )
            self.echo_debug(assigned_metadata)
            self.echo_info(
                "Assigned metadata to a sample {}".format(self.sample_id)
            )
        except client.APIClientError as err:
            self.echo_debug(err)
            if err.status_code == 400:
                self.echo_error("There was an error assigning metadata.")
            elif err.status_code == 404:
                self.echo_error(
                    "Sample {} does not exist or you do not have "
                    "permission required to access it.".format(self.sample_id)
                )
            raise

    def _valid_json(self, metadata):
        try:
            json.loads(metadata)
            return True
        except ValueError as err:
            self.echo_error(err)
            return False
