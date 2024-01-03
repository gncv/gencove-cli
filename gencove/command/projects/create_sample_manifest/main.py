"""Create project's batch executor."""
import os

from gencove import client  # noqa: I100
from gencove.command.base import Command
from gencove.exceptions import ValidationError


class CreateSampleManifest(Command):
    """Create project's sample manifest executor."""

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        project_id,
        sample_manifest,
        credentials,
        options,
    ):
        super().__init__(credentials, options)
        self.project_id = project_id
        self.sample_manifest = sample_manifest

    def initialize(self):
        """Initialize list subcommand."""
        self.login()

    def validate(self):
        """Validate command input.

        Raises:
            ValidationError - if something is wrong with command parameters.
        """
        if self.sample_manifest[-4:] != ".csv" and self.sample_manifest[-5:] != ".xlsx":
            raise ValidationError(
                "sample_manifest argument must be a local path to a CSV or XLSX file"
            )

        if not os.path.exists(self.sample_manifest):
            raise ValidationError(
                "supplied path to sample_manifest argument does not exist"
            )

    def execute(self):
        """Make a request to create a sample manifest for given project."""
        self.echo_debug(f"Creating sample manifest for project {self.project_id} ")

        try:
            created_sample_manifest_details = self.api_client.create_sample_manifest(
                project_id=self.project_id, sample_manifest=self.sample_manifest
            )
            self.echo_debug(created_sample_manifest_details)
            self.echo_info(
                f"Successfully uploaded sample manifest to project {self.project_id}"
            )
        except client.APIClientError as err:
            self.echo_debug(err)
            if err.status_code == 400:
                self.echo_warning("There was an error creating the sample manifest.")
                self.echo_info("The following error was returned:")
                self.echo_info(err.message)
            elif err.status_code == 404:
                self.echo_warning(f"Project {self.project_id} does not exist.")
            else:
                raise
