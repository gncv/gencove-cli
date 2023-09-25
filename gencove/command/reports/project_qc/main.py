"""Project QC report executor."""
from pathlib import Path

from gencove import client  # noqa: I100
from gencove.command.base import Command
from gencove.command.download.utils import download_file


class ProjectQCReport(Command):
    """Get sample manifest executor."""

    def __init__(
        self,
        project_id,
        destination,
        credentials,
        options,
    ):
        super().__init__(credentials, options)
        self.project_id = project_id
        self.destination = destination

    def initialize(self):
        """Initialize list subcommand."""
        self.login()

    def validate(self):
        """Validate command input.

        Raises:
            ValidationError - if something is wrong with command parameters.
        """

    def execute(self):
        """Request to get project QC report and download it."""
        self.echo_debug(f"Retrieving project QC report for project {self.project_id}")

        try:
            sample_manifest = self.api_client.get_sample_manifest(
                manifest_id=self.manifest_id,
            )
            dst = (
                Path(self.destination)
                / str(sample_manifest.id)
                / sample_manifest.file_name
            )
            dst.parent.mkdir(exist_ok=True, parents=True)
            self.echo_info(
                f"Downloading manifest with ID {sample_manifest.id} to {dst}"
            )
            download_file(
                file_path=str(dst),
                download_url=sample_manifest.file.download_url,
                no_progress=True,
            )
        except client.APIClientError as err:
            self.echo_debug(err)
            if err.status_code == 400:
                self.echo_warning("There was an error retrieving the sample manifest.")
                self.echo_info("The following error was returned:")
                self.echo_info(err.message)
            elif err.status_code == 404:
                self.echo_warning(
                    f"Sample manifest with ID {self.manifest_id} does not exist or "
                    "you do not have access."
                )
            else:
                raise
