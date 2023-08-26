"""Create project's batch executor."""
import os
from gencove import client  # noqa: I100
from gencove.command.base import Command
from gencove.exceptions import ValidationError


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
        if not os.path.isdir(self.destination) or not os.path.exists(self.destination):
            raise ValidationError(
                "destination argument must be a directory that exists"
            )

    def execute(self):
        """Make a request to download all sample manifests from a given project."""
        self.echo_debug(f"Retrieving sample manifests for project {self.project_id}")

        try:
            created_sample_manifest_details = self.api_client.get_sample_manifests(
                project_id=self.project_id
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
