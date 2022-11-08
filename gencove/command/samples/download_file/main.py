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
        checksum,
    ):
        super().__init__(credentials, options)
        self.sample_id = sample_id
        self.file_type = file_type
        self.destination = destination
        self.no_progress = no_progress
        self.checksum = checksum

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
                    f"Sample {self.sample_id} file {self.file_type} does not "
                    "exist or you do not have permission required to access it."
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
                f"Sample with id {self.sample_id} not found. "
                "Are you using client id instead of sample id?"
            )
            return

        self.echo_debug(
            f"Processing sample id {sample.id}, status {sample.last_status.status}"
        )

        if not ALLOWED_ARCHIVE_STATUSES_RE.match(sample.archive_last_status.status):
            raise ValidationError(
                f"Sample with id {sample.id} is archived and cannot be downloaded - "
                "please restore the sample and try again."
            )

        sample_file_types = {file.file_type for file in sample.files}
        if self.file_type not in sample_file_types:
            raise ValidationError(
                f"Sample with id {sample.id} does not have any files with "
                f"file type {self.file_type}. Valid file types for this sample are: "
                f"{', '.join(sorted(sample_file_types))}."
            )

        file_to_download = None

        for sample_file in sample.files:
            # pylint: disable=E0012,C0330
            if self.file_type == sample_file.file_type:
                file_to_download = sample_file
                break

        if file_to_download is None or file_to_download.download_url is None:
            self.echo_warning(
                f"File not found for sample with id {self.sample_id} "
                f"and file type {self.file_type}"
            )
        else:
            download_file(
                self.destination,
                file_to_download.download_url,
                self.no_progress,
            )
            writing_to_stdout = self.destination.isatty()
            if not writing_to_stdout and self.checksum:
                try:
                    checksum = self.api_client.get_file_checksum(
                        file_to_download.id,
                        filename=self.destination.name,
                    )
                    self.create_checksum_file(self.destination.name, checksum)
                except client.APIClientTooManyRequestsError:
                    self.echo_debug(
                        "Request was throttled for checksum file, trying again"
                    )
                    raise

    def create_checksum_file(self, file_path, checksum_sha256):
        """Create checksum file.

        Args:
            file_path (str): File path of the original file,
                will append .sha256
            checksum_sha256 (str): Checksum (sha256) value for the file

        Returns:
            None
        """
        checksum_path = f"{file_path}.sha256"
        self.echo_debug(f"Adding checksum file: {checksum_path}")
        with open(checksum_path, "w", encoding="utf-8") as checksum_file:
            checksum_file.write(checksum_sha256)
