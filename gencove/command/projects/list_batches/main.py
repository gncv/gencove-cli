"""List project's batch types subcommand."""

import backoff

import requests

# pylint: disable=wrong-import-order
from gencove.client import APIClientError  # noqa: I100
from gencove.command.base import Command, ValidationError
from gencove.command.utils import is_valid_uuid

from .exceptions import BatchesError
from .utils import get_line


class ListBatches(Command):
    """List batches command executor."""

    def __init__(self, project_id, credentials, options):
        super(ListBatches, self).__init__(credentials, options)

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
            error_message = "Project ID is not valid. Exiting."
            self.echo_warning(error_message, err=True)
            raise ValidationError(error_message)

    def execute(self):
        self.echo_debug("Retrieving project's batches:")

        for batches in self.get_paginated_batches():
            if not batches:
                self.echo_debug("No matching batches were found.")
                return

            for batch in batches:
                self.echo(get_line(batch))

    def get_paginated_batches(self):
        """Paginate over all batches for the destination.

        Yields:
            paginated lists of batches
        """
        more = True
        next_link = None
        while more:
            self.echo_debug("Get batches page")
            try:
                resp = self.get_batches(next_link)
                yield resp["results"]
                next_link = resp["meta"]["next"]
                more = next_link is not None
            except APIClientError as err:
                self.echo_debug(err)
                raise BatchesError

    @backoff.on_exception(
        backoff.expo,
        (requests.exceptions.ConnectionError, requests.exceptions.Timeout),
        max_tries=2,
        max_time=30,
    )
    def get_batches(self, next_link=None):
        """Get batches page."""
        return self.api_client.get_project_batches(
            project_id=self.project_id, next_link=next_link,
        )
