"""Download project's merged VCF file executor."""
import backoff

from ... import download
from ...base import Command
from ...utils import is_valid_uuid
from .... import client
from ....exceptions import ValidationError


class GetMergedVCF(Command):
    """Download project's merged VCF file executor."""

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        project_id,
        output_filename,
        credentials,
        options,
        no_progress,
    ):
        super().__init__(credentials, options)
        self.project_id = project_id
        self.output_filename = output_filename
        self.no_progress = no_progress

    def initialize(self):
        """Initialize subcommand."""
        self.login()

    def validate(self):
        """Validate command input.

        Raises:
            ValidationError - if something is wrong with command parameters.
        """
        if is_valid_uuid(self.project_id) is False:
            raise ValidationError("Project ID is not valid. Exiting.")

    @backoff.on_exception(
        backoff.expo,
        (client.APIClientTimeout),
        max_tries=5,
        max_time=30,
    )
    def execute(self):
        """Download merged VCF file for a given project."""
        self.echo_debug(f"Downloading merged VCF file for project {self.project_id}")
        try:
            project = self.api_client.get_project(self.project_id)
            self.echo_debug(project)
            merged_vcf = next(
                (f for f in project.files if f.file_type == "impute-vcf-merged"),
                None,
            )
            if merged_vcf is None:
                raise ValidationError(
                    f"No files to process for project {self.project_id}"
                )
            download_path = (
                self.output_filename
                if self.output_filename
                else download.utils.get_filename_from_download_url(
                    merged_vcf.download_url
                )
            )
            download.utils.download_file(
                download_path,
                merged_vcf.download_url,
                no_progress=self.no_progress,
            )
        except client.APIClientError as err:
            self.echo_debug(err)
            if err.status_code == 404:
                self.echo_error(f"Project {self.project_id} does not exist.")
            raise
