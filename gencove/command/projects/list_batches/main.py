"""List project's batches subcommand."""

import backoff

# pylint: disable=wrong-import-order
from gencove import client  # noqa: I100
from gencove.command.base import Command
from gencove.command.utils import is_valid_uuid
from gencove.exceptions import ValidationError

from .utils import get_line


class ListBatches(Command):
    """List batches command executor."""

    def __init__(self, project_id, credentials, options):
        super().__init__(credentials, options)
        self.project_id = project_id

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

    def execute(self):
        self.echo_debug("Retrieving project's batches:")

        try:
            for batches in self.get_paginated_batches():
                if not batches:
                    self.echo_debug("No matching batches were found.")
                    return

                for batch in batches:
                    self.echo_data(get_line(batch))
        except client.APIClientError as err:
            self.echo_debug(err)
            if err.status_code == 400:
                self.echo_warning(
                    "There was an error listing project batches."
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
                raise

    def get_paginated_batches(self):
        """Paginate over all batches for the destination.

        Yields:
            paginated lists of batches
        """
        more = True
        next_link = None
        while more:
            self.echo_debug("Get batches page")
            resp = self.get_batches(next_link)
            yield resp["results"]
            next_link = resp["meta"]["next"]
            more = next_link is not None

    @backoff.on_exception(
        backoff.expo,
        (client.APIClientTimeout),
        max_tries=2,
        max_time=30,
    )
    def get_batches(self, next_link=None):
        """Get batches page."""
        return self.api_client.get_project_batches(
            project_id=self.project_id, next_link=next_link
        )
