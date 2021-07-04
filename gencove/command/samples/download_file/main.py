"""Download sample file subcommand."""

import backoff

import requests

from gencove.command.download.constants import (  # noqa: I100
    ALLOWED_ARCHIVE_STATUSES_RE,
)

from .utils import download_file, fatal_process_sample_error
from ...base import Command
from ...utils import is_valid_uuid
from .... import client
from ....exceptions import ValidationError


class DownloadFile(Command):
    """Download file command executor."""

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        sample_id,
        file_type,
        destination,
        credentials,
        options,
        no_progress,
    ):
        super().__init__(credentials, options)
        self.sample_id = sample_id
        self.file_type = file_type
        self.destination = destination
        self.no_progress = no_progress

    def initialize(self):
        """Initialize download-file subcommand."""
        self.login()

    def validate(self):
        """Validate command input.

        Raises:
            ValidationError - if something is wrong with command parameters.
        """

        if is_valid_uuid(self.sample_id) is False:
            raise ValidationError("Sample ID is not valid. Exiting.")

    def execute(self):
        self.echo_debug("Retrieving sample file:")

        try:
            self.get_file()
        except client.APIClientError as err:
            self.echo_debug(err)
            if err.status_code == 404:
                self.echo_error(
                    "Sample {} file {} does not exist or you do not have "
                    "permission required to access it.".format(
                        self.sample_id, self.file_type
                    )
                )
            raise

    @backoff.on_exception(
        backoff.expo,
        requests.exceptions.HTTPError,
        giveup=fatal_process_sample_error,
        max_tries=10,
    )
    def get_file(self):
        """Retrieves file and writes it to destination"""
        try:
            sample = self.api_client.get_sample_details(self.sample_id)
        except client.APIClientError:
            self.echo_warning(
                "Sample with id {} not found. "
                "Are you using client id instead of sample id?".format(
                    self.sample_id
                )
            )
            return

        self.echo_debug(
            "Processing sample id {}, status {}".format(
                sample.id, sample.last_status.status
            )
        )

        if not ALLOWED_ARCHIVE_STATUSES_RE.match(
            sample.archive_last_status.status
        ):
            raise ValidationError(
                "Sample with id {} is archived and cannot be downloaded - "
                "please restore the sample and try again.".format(sample.id)
            )

        file_to_download = None

        for sample_file in sample.files:
            # pylint: disable=E0012,C0330
            if self.file_type == sample_file.file_type:
                file_to_download = sample_file
                break

        if file_to_download is None or file_to_download.download_url is None:
            self.echo_warning(
                "File not found for sample with id {} and file type {}".format(
                    self.sample_id, self.file_type
                )
            )
        else:
            download_file(
                self.destination,
                file_to_download.download_url,
                self.no_progress,
            )
