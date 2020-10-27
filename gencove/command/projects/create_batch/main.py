"""Create project's batch executor."""
import backoff

import requests

from gencove import client  # noqa: I100
from gencove.command.base import Command
from gencove.command.projects.list_batches.utils import get_line
from gencove.command.utils import is_valid_uuid
from gencove.exceptions import ValidationError

from .exceptions import BatchCreateError


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
            raise ValidationError(
                "You must provide value for --batch-type. Exiting."
            )

        if not self.batch_name:
            raise ValidationError(
                "You must provide value for --batch-name. Exiting."
            )

        if is_valid_uuid(self.project_id) is False:
            raise ValidationError("Project ID is not valid. Exiting.")

        if self.sample_ids:
            if not all([is_valid_uuid(s_id) for s_id in self.sample_ids]):
                raise ValidationError(
                    "Not all sample IDs are valid. Exiting."
                )

    @backoff.on_exception(
        backoff.expo,
        (requests.exceptions.ConnectionError, requests.exceptions.Timeout),
        max_tries=5,
        max_time=30,
    )
    def execute(self):
        """Make a request to create a batch for given project."""
        self.echo_debug(
            "Creating batch for project {} and batch key {}".format(
                self.project_id, self.batch_name
            )
        )

        try:
            created_batches_details = self.api_client.create_project_batch(
                project_id=self.project_id,
                batch_type=self.batch_type,
                batch_name=self.batch_name,
                sample_ids=self.sample_ids,
            )
            self.echo_debug(created_batches_details)
            for batch in created_batches_details["results"]:
                self.echo_data(get_line(batch))
        except client.APIClientError as err:
            self.echo_debug(err)
            if err.status_code == 400:
                self.echo_warning(
                    "There was an error creating project batches."
                )
                self.echo_info("The following error was returned:")
                self.echo_info(err.message)
            elif err.status_code == 404:
                self.echo_warning(
                    "Project {} does not exist or you do not have "
                    "permission required to access it.".format(
                        self.project_id
                    )
                )
            else:
                raise BatchCreateError  # pylint: disable=W0707
