"""Request project cancel samples"""
from gencove import client  # noqa: I100
from gencove.command.base import Command


class CancelSamples(Command):
    """Cancel project's samples."""

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        project_id,
        sample_ids,
        credentials,
        options,
    ):
        super().__init__(credentials, options)
        self.project_id = project_id
        self.sample_ids = sample_ids

    def initialize(self):
        """Initialize list subcommand."""
        self.login()

    def validate(self):
        """Validate command input.

        Raises:
            ValidationError - if something is wrong with command parameters.
        """

    def execute(self):
        """Make a request to request samples cancel for given project."""
        self.echo_debug(
            f"Requesting to cancel samples in project {self.project_id} for "
            f"samples {self.sample_ids}"
        )

        try:
            cancel_project_samples_details = self.api_client.cancel_project_samples(
                project_id=self.project_id,
                sample_ids=self.sample_ids,
            )

            self.echo_debug(cancel_project_samples_details)
            self.echo_info("The following samples have been canceled successfully:")
            for sample in self.sample_ids:
                self.echo_info(f"\t{sample}")
        except client.APIClientError as err:
            self.echo_debug(err)
            if err.status_code == 400:
                self.echo_warning(
                    "There was an error requesting cancel project samples."
                )
                self.echo_info("The following error was returned:")
                self.echo_info(err.message)
            elif err.status_code == 404:
                self.echo_warning(f"Project {self.project_id} does not exist.")
            raise
