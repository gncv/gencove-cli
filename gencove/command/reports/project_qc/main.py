"""Project QC report executor."""
from pathlib import Path

from gencove import client  # noqa: I100
from gencove.command.base import Command
from gencove.command.utils import extract_filename_from_headers


class ProjectQCReport(Command):
    """Get project QC report executor."""

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        project_id,
        columns,
        output_filename,
        credentials,
        options,
    ):
        super().__init__(credentials, options)
        self.project_id = project_id
        self.columns = columns
        self.output_filename = output_filename

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
        self.echo_info(
            f"Retrieving project QC report for project with ID {self.project_id}"
        )

        try:
            project_qc_report = self.api_client.get_project_qc_report(
                project_id=self.project_id, columns=self.columns
            )

            if not self.output_filename:
                filename = extract_filename_from_headers(
                    headers=project_qc_report.headers
                )
                if not filename:
                    filename = "project-qc-report.csv"
                self.output_filename = Path.cwd() / filename
            else:
                Path(self.output_filename).parent.mkdir(exist_ok=True, parents=True)
            with open(self.output_filename, "wb") as filename:
                filename.write(project_qc_report.content)
            self.echo_info(
                f"Saved project QC report CSV for project {self.project_id} "
                f"to {Path(self.output_filename).resolve()}"
            )
        except client.APIClientError as err:
            self.echo_debug(err)
            if err.status_code == 400:
                self.echo_warning(
                    "There was an error retrieving the project QC report."
                )
                self.echo_info("The following error was returned:")
                self.echo_info(err.message)
            elif err.status_code == 404:
                self.echo_warning(
                    f"Project with ID {self.project_id} does not exist or "
                    "you do not have access."
                )
            else:
                raise
