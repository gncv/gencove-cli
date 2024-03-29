"""Create project's batch executor."""
from gencove import client  # noqa: I100
from gencove.command.base import Command
from gencove.command.projects.list_batches.utils import get_line
from gencove.exceptions import ValidationError


class CreateBatch(Command):
    """Create project's batch executor."""

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        project_id,
        batch_type,
        batch_name,
        sample_ids,
        credentials,
        options,
    ):
        super().__init__(credentials, options)
        self.project_id = project_id
        self.batch_type = batch_type
        self.batch_name = batch_name
        self.sample_ids = sample_ids

    def initialize(self):
        """Initialize list subcommand."""
        self.login()

    def validate(self):
        """Validate command input.

        Raises:
            ValidationError - if something is wrong with command parameters.
        """
        if not self.batch_type:
            raise ValidationError("You must provide value for --batch-type. Exiting.")

        if not self.batch_name:
            raise ValidationError("You must provide value for --batch-name. Exiting.")

    # no retry for timeouts in order to avoid duplicate heavy operations on
    # the backend
    def execute(self):
        """Make a request to create a batch for given project."""
        self.echo_debug(
            f"Creating batch for project {self.project_id} and "
            f"batch key {self.batch_name}"
        )

        try:
            created_batches_details = self.api_client.create_project_batch(
                project_id=self.project_id,
                batch_type=self.batch_type,
                batch_name=self.batch_name,
                sample_ids=self.sample_ids,
            )
            self.echo_debug(created_batches_details)
            for batch in created_batches_details.results:
                self.echo_data(get_line(batch))
        except client.APIClientError as err:
            self.echo_debug(err)
            if err.status_code == 400:
                self.echo_warning("There was an error creating project batches.")
                self.echo_info("The following error was returned:")
                self.echo_info(err.message)
            elif err.status_code == 404:
                self.echo_warning(f"Project {self.project_id} does not exist.")
            else:
                raise
