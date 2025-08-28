"""Download project's jointcalled VCF files executor."""
import os

import backoff

from ... import download
from ...base import Command
from .... import client


class GetJointcalledVCF(Command):
    """Download project's jointcalled VCF files executor."""

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        project_id,
        output_folder,
        credentials,
        options,
        no_progress,
    ):
        super().__init__(credentials, options)
        self.project_id = project_id
        self.output_folder = output_folder or "."
        self.no_progress = no_progress

    def initialize(self):
        """Initialize subcommand."""
        self.login()

    def validate(self):
        """Validate command input."""

    @backoff.on_exception(
        backoff.expo,
        (client.APIClientTimeout),
        max_tries=5,
        max_time=30,
    )
    def execute(self):
        """Download jointcalled VCF files for a given project."""
        self.echo_debug(
            f"Downloading jointcalled VCF files for project {self.project_id}"
        )
        try:
            project = self.api_client.get_project(self.project_id)
            self.echo_debug(project)
            if not project.files:
                self.echo_error(
                    f"Project {self.project_id} has no jointcalled VCF files."
                )
                return

            for file in project.files:
                if file.file_type in ["jointcalled-vcf", "jointcalled-vcf_indexed"]:
                    self.echo_debug(
                        f"Downloading jointcalled VCF file {file.file_type}"
                    )
                    filename = download.utils.get_filename_from_download_url(
                        file.download_url
                    )
                    download_path = os.path.join(self.output_folder, filename)
                    self.echo_debug(
                        f"Downloading jointcalled VCF file to {download_path}"
                    )
                    download.utils.download_file(
                        download_path,
                        file.download_url,
                        no_progress=self.no_progress,
                    )
        except client.APIClientError as err:
            self.echo_debug(err)
            if err.status_code == 404:
                self.echo_error(f"Project {self.project_id} does not exist.")
            raise
