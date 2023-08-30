"""Create project's batch executor."""
from pathlib import Path

from gencove import client  # noqa: I100
from gencove.command.base import Command
from gencove.command.download.utils import download_file
from gencove.models import SampleManifests


class GetSampleManifests(Command):
    """Get project sample manifests executor."""

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
        """Request to download all sample manifests from a project."""
        self.echo_debug(f"Retrieving sample manifests for project {self.project_id}")

        try:
            sample_manifests = self.api_client.get_sample_manifests(
                project_id=self.project_id
            )
            sample_manifests_validated = SampleManifests(results=sample_manifests)
            self.echo_debug(sample_manifests_validated)
            for sample_manifest in sample_manifests_validated.results:
                dst = (
                    Path(self.destination)
                    / str(sample_manifest.id)
                    / sample_manifest.file_name
                )
                dst.parent.mkdir(exist_ok=True, parents=True)
                self.echo_info(
                    f"Downloading sample manifest with ID"
                    f" {sample_manifest.id} to {dst}"
                )
                download_file(
                    file_path=str(dst),
                    download_url=sample_manifest.file.download_url,
                    no_progress=True,
                )
        except client.APIClientError as err:
            self.echo_debug(err)
            if err.status_code == 400:
                self.echo_warning(
                    "There was an error retrieving the sample "
                    "manifests for this project."
                )
                self.echo_info("The following error was returned:")
                self.echo_info(err.message)
            elif err.status_code == 404:
                self.echo_warning(f"Project {self.project_id} does not exist.")
            else:
                raise
