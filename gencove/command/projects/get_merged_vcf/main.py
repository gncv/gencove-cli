"""Download project's merged VCF file executor."""
import backoff

import requests

from ... import download
from ...base import Command
from ...utils import is_valid_uuid
from .... import client
from ....exceptions import ValidationError


class GetMergedVCF(Command):
    """Download project's merged VCF file executor."""

    def __init__(
        self,
        project_id,
        output_filename,
        credentials,
        options,
    ):
        super().__init__(credentials, options)
        self.project_id = project_id
        self.output_filename = output_filename

    def initialize(self):
        """Initialize subcommand."""
        self.login()

    def validate(self):
        """Validate command input.

        Raises:
            ValidationError - if something is wrong with command parameters.
        """
        if is_valid_uuid(self.project_id) is False:
            error_message = "Project ID is not valid. Exiting."
            self.echo_error(error_message)
            raise ValidationError(error_message)

    @backoff.on_exception(
        backoff.expo,
        (requests.exceptions.ConnectionError, requests.exceptions.Timeout),
        max_tries=5,
        max_time=30,
    )
    def execute(self):
        """Download merged VCF file for a given project."""
        self.echo_debug(
            "Downloading merged VCF file for project {}".format(
                self.project_id
            )
        )
        try:
            project = self.api_client.get_project(self.project_id)
            self.echo_debug(project)
            merged_vcf = next(
                (
                    f
                    for f in project["files"]
                    if f["file_type"] == "impute-vcf-merged"
                ),
                None,
            )
            if merged_vcf is None:
                error_message = "No files to process for project {}".format(
                    self.project_id
                )
                self.echo_error(error_message)
                raise ValidationError(error_message)
            download_path = (
                self.output_filename
                if self.output_filename
                else download.utils.get_filename_from_download_url(
                    merged_vcf["download_url"]
                )
            )
            download.utils.download_file(
                download_path, merged_vcf["download_url"]
            )
        except client.APIClientError as err:
            self.echo_debug(err)
            if err.status_code == 400:
                self.echo_error("There was an error getting the merged file.")
            elif err.status_code == 404:
                self.echo_error(
                    "Project {} does not exist or you do not have "
                    "permission required to access it.".format(
                        self.project_id
                    )
                )
            raise
