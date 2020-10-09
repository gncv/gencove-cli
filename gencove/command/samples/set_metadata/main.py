"""Set sample metadata subcommand."""

import json
import backoff

import requests

from gencove import client
from gencove.command.base import Command
from gencove.command.utils import is_valid_uuid
from gencove.exceptions import ValidationError


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
            error_message = "Sample ID is not valid. Exiting."
            self.echo_warning(error_message, err=True)
            raise ValidationError(error_message)

        if not self._valid_json(self.json_metadata):
            error_message = "Metadatata JSON is not valid. Exiting."
            self.echo_warning(error_message, err=True)
            raise ValidationError(error_message)

    @backoff.on_exception(
        backoff.expo,
        (requests.exceptions.ConnectionError, requests.exceptions.Timeout),
        max_tries=5,
        max_time=30,
    )
    def execute(self):
        """Make a request to assign given metadata to a specified sample."""

        self.echo_debug(
            "Assigning metadata to a sample {}".format(self.sample_id)
        )

        try:
            assigned_metadata = self.api_client.set_metadata(
                self.sample_id, self.json_metadata
            )
            self.echo_debug(assigned_metadata)
            self.echo(
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
            self.json_metadata = json.loads(metadata)
            return True
        except ValueError as err:
            self.echo_error(err)
            return False
