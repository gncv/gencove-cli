"""Monthly usage report executor."""
from pathlib import Path

from gencove import client  # noqa: I100
from gencove.command.base import Command
from gencove.command.utils import extract_filename_from_headers


class MonthlyUsageReport(Command):
    """Monthly usage report executor."""

    def __init__(  # pylint: disable=too-many-arguments,invalid-name
        self,
        from_,
        to,
        output_filename,
        credentials,
        options,
    ):
        super().__init__(credentials, options)
        self.from_ = from_
        self.to = to
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
        self.echo_info("Retrieving monthly usage report for organization")

        try:
            monthly_usage_report = (
                self.api_client.get_organization_monthly_usage_report(
                    from_=self.from_, to=self.to
                )
            )

            if not self.output_filename:
                filename = extract_filename_from_headers(
                    headers=monthly_usage_report.headers
                )
                if not filename:
                    filename = "monthly-usage-report.csv"
                self.output_filename = Path.cwd() / filename
            else:
                Path(self.output_filename).parent.mkdir(exist_ok=True, parents=True)

            with open(self.output_filename, "wb") as filename:
                filename.write(monthly_usage_report.content)
            self.echo_info(
                f"Saved organization monthly usage report CSV "
                f"to {Path(self.output_filename).resolve()}"
            )
        except client.APIClientError as err:
            self.echo_debug(err)
            if err.status_code == 400:
                self.echo_warning(
                    "There was an error retrieving the monthly usage report."
                )
                self.echo_info("The following error was returned:")
                self.echo_info(err.message)
            elif err.status_code == 404:
                self.echo_warning("You do not have access to this report")
            else:
                raise
