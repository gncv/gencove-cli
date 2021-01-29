"""Request project's samples restore."""
import backoff

import requests

from gencove import client  # noqa: I100
from gencove.command.base import Command
from gencove.command.utils import is_valid_uuid
from gencove.exceptions import ValidationError

from .exceptions import SamplesRestoreError


class RestoreSamples(Command):
    """Restore project's samples."""

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
        if is_valid_uuid(self.project_id) is False:
            raise ValidationError("Project ID is not valid. Exiting.")

        if self.sample_ids:
            if not all([is_valid_uuid(s_id) for s_id in self.sample_ids]):
                raise ValidationError(
                    "Not all sample IDs are valid. Exiting."
                )
        else:
            raise ValidationError("Missing sample IDs. Exiting.")

    @backoff.on_exception(
        backoff.expo,
        (requests.exceptions.ConnectionError, requests.exceptions.Timeout),
        max_tries=5,
        max_time=30,
    )
    def execute(self):
        """Make a request to request samples restore for given project."""
        self.echo_debug(
            "Requesting samples restore in project {} for samples {} ".format(
                self.project_id, self.sample_ids
            )
        )

        try:
            restored_project_samples_details = (
                self.api_client.restore_project_samples(
                    project_id=self.project_id,
                    sample_ids=self.sample_ids,
                )
            )
            self.echo_debug(restored_project_samples_details)
            self.echo_info("Request to restore samples accepted.")
        except client.APIClientError as err:
            self.echo_debug(err)
            if err.status_code == 400:
                self.echo_warning(
                    "There was an error requesting project samples restore."
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
                raise SamplesRestoreError  # pylint: disable=W0707
