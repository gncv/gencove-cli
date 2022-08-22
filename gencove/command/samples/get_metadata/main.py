"""Get sample metadata subcommand."""

import json
import os

import backoff

from ...base import Command
from ...utils import is_valid_uuid
from .... import client
from ....exceptions import ValidationError


class GetMetadata(Command):
    """Get metadata command executor."""

    def __init__(self, sample_id, output_filename, credentials, options):
        super().__init__(credentials, options)
        self.sample_id = sample_id
        self.output_filename = output_filename

    def initialize(self):
        """Initialize get-metadata subcommand."""
        self.login()

    def validate(self):
        """Validate command input.

        Raises:
            ValidationError - if something is wrong with command parameters.
        """

        if is_valid_uuid(self.sample_id) is False:
            raise ValidationError("Sample ID is not valid. Exiting.")

    def execute(self):
        self.echo_debug("Retrieving sample metadata:")

        try:
            metadata = self.get_metadata()
            self.output_metadata(metadata)

        except client.APIClientError as err:
            self.echo_debug(err)
            if err.status_code == 404:
                self.echo_error(f"Sample metadata {self.sample_id} does not exist.")
            raise

    @backoff.on_exception(
        backoff.expo,
        (client.APIClientTimeout),
        max_tries=2,
        max_time=30,
    )
    def get_metadata(self):
        """Get metadata page."""
        response = self.api_client.get_metadata(sample_id=self.sample_id)
        # API always returns a dictionary with a "metadata" key
        return response.metadata

    def output_metadata(self, metadata):
        """Output reformatted metadata JSON."""
        self.echo_debug("Outputting JSON.")
        if self.output_filename == "-":
            self.echo_data(json.dumps(metadata, indent=4, cls=client.CustomEncoder))
        else:
            dirname = os.path.dirname(self.output_filename)
            if dirname and not os.path.exists(dirname):
                os.makedirs(dirname)
            with open(self.output_filename, "w", encoding="utf-8") as json_file:
                json_file.write(
                    json.dumps(metadata, indent=4, cls=client.CustomEncoder)
                )
            self.echo_info(f"Sample metadata saved to {self.output_filename}")
