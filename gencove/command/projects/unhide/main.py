"""Request to unhide projects"""
from gencove import client  # noqa: I100
from gencove.command.base import Command


class Unhide(Command):
    """Unhide projects."""

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        project_ids,
        credentials,
        options,
    ):
        super().__init__(credentials, options)
        self.project_ids = project_ids

    def initialize(self):
        """Initialize list subcommand."""
        self.login()

    def validate(self):
        """Validate command input.

        Raises:
            ValidationError - if something is wrong with command parameters.
        """

    def execute(self):
        """Make a request to request unhide projects."""
        self.echo_debug(f"Requesting to unhide projects {self.project_ids}")

        try:
            unhidden_projects_details = self.api_client.unhide_projects(
                project_ids=self.project_ids,
            )

            self.echo_debug(unhidden_projects_details)
            self.echo_info("The following projects have been unhidden successfully:")
            for project in self.project_ids:
                self.echo_info(f"\t{project}")
        except client.APIClientError as err:
            self.echo_debug(err)
            if err.status_code == 400:
                self.echo_warning(
                    "There was an error with the unhide projects request."
                )
                self.echo_info("The following error was returned:")
                self.echo_info(err.message)
            elif err.status_code == 404:
                self.echo_warning(
                    f"Some of the projects in the provided list {self.project_ids} "
                    f"do not exist."
                )
            else:
                raise
