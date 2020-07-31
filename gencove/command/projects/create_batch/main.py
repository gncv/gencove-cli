"""Create project's batch executor."""
import backoff

import requests

from gencove import client  # noqa: I100
from gencove.command.base import Command, ValidationError
from gencove.command.utils import is_valid_uuid

from .exceptions import BatchCreateError


class CreateBatch(Command):
    """Create project's batch executor."""

    def __init__(
        self,
        project_id,
        batch_type,
        batch_name,
        sample_ids,
        credentials,
        options,
    ):
        super(CreateBatch, self).__init__(credentials, options)
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
            error_message = (
                "You must provide value for --batch-type. Exiting."
            )
            self.echo_warning(error_message, err=True)
            raise ValidationError(error_message)

        if not self.batch_name:
            error_message = (
                "You must provide value for --batch-name. Exiting."
            )
            self.echo_warning(error_message, err=True)
            raise ValidationError(error_message)

        if is_valid_uuid(self.project_id) is False:
            error_message = "Project ID is not valid. Exiting."
            self.echo_warning(error_message, err=True)
            raise ValidationError(error_message)

        if self.sample_ids:
            if not all([is_valid_uuid(s_id) for s_id in self.sample_ids]):
                error_message = "Not all sample IDs are valid. Exiting."
                self.echo_warning(error_message, err=True)
                raise ValidationError(error_message)

    def execute(self):
        """Make a request to create a batch for given project.
        """
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
        except client.APIClientError as err:
            # TODO catching errors is not working as expected!
            # parsing of error fails
            if err.status_code == 400:
                self.echo(err.message)
                raise BatchCreateError
            raise err
