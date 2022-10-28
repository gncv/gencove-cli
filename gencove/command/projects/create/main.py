"""Create project executor."""
from gencove import client  # noqa: I100
from gencove.command.base import Command

from .utils import get_line


class CreateProject(Command):
    """Create project executor."""

    def __init__(
        self,
        project_name,
        pipeline_capability_id,
        credentials,
        options,
    ):
        super().__init__(credentials, options)
        self.project_name = project_name
        self.pipeline_capability_id = pipeline_capability_id

    def initialize(self):
        """Initialize create subcommand."""
        self.login()

    def validate(self):
        """Validate command input."""

    def execute(self):
        """Make a request to create a project."""
        self.echo_debug(f"Creating a project {self.project_name}.")

        try:
            created_project_details = self.api_client.create_project(
                project_name=self.project_name,
                pipeline_capability_id=self.pipeline_capability_id,
            )
            self.echo_debug(created_project_details)
            self.echo_data(get_line(created_project_details))
        except client.APIClientError as err:
            self.echo_debug(err)
            if err.status_code == 400:
                self.echo_warning("There was an error creating a project.")
                self.echo_info("The following error was returned:")
                self.echo_info(err.message)
            raise
