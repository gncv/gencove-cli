"""Get project batch's deliverable subcommand."""

import backoff

# pylint: disable=wrong-import-order
from gencove import client  # noqa: I100
from gencove.command.base import Command
from gencove.command.utils import is_valid_uuid
from gencove.exceptions import ValidationError

from ... import download


class GetBatch(Command):
    """Get batch command executor."""

    # pylint: disable=too-many-arguments
    def __init__(
        self, batch_id, output_filename, credentials, options, no_progress
    ):
        super().__init__(credentials, options)
        self.batch_id = batch_id
        self.output_filename = output_filename
        self.no_progress = no_progress

    def initialize(self):
        """Initialize list subcommand."""
        self.login()

    def validate(self):
        """Validate command input.

        Raises:
            ValidationError - if something is wrong with command parameters.
        """

        if is_valid_uuid(self.batch_id) is False:
            raise ValidationError("Batch ID is not valid. Exiting.")

    def execute(self):
        self.echo_debug("Retrieving batch:")

        try:
            batch = self.get_batch()
            if len(batch["files"]) == 0:
                raise ValidationError(
                    "There are no deliverables available for batch {}.".format(
                        self.batch_id
                    )
                )
            if len(batch["files"]) > 1:
                self.echo_warning(
                    "There is more than one deliverable available for "
                    "batch {}.".format(self.batch_id)
                )
            deliverable = batch["files"][0]
            download_path = (
                self.output_filename
                if self.output_filename
                else download.utils.get_filename_from_download_url(
                    deliverable["download_url"]
                )
            )
            download.utils.download_file(
                download_path,
                deliverable["download_url"],
                no_progress=self.no_progress,
            )

        except client.APIClientError as err:
            self.echo_debug(err)
            if err.status_code == 400:
                self.echo_warning("There was an error getting the batch.")
                self.echo_info("The following error was returned:")
                self.echo_info(err.message)
            elif err.status_code == 404:
                self.echo_warning(
                    "Batch {} does not exist or you do not have "
                    "permission required to access it.".format(self.batch_id),
                )
            else:
                raise

    @backoff.on_exception(
        backoff.expo,
        (client.APIClientTimeout),
        max_tries=2,
        max_time=30,
    )
    def get_batch(self):
        """Get batches page."""
        return self.api_client.get_batch(batch_id=self.batch_id)
