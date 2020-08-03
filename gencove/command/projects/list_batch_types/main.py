"""List project's batch types subcommand."""

import backoff

import requests

# pylint: disable=wrong-import-order
from gencove import client  # noqa: I100
from gencove.command.base import Command, ValidationError
from gencove.command.utils import is_valid_uuid

from .exceptions import BatchTypesError
from .utils import get_line


class ListBatchTypes(Command):
    """List batch types command executor."""

    def __init__(self, project_id, credentials, options):
        super(ListBatchTypes, self).__init__(credentials, options)

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
        self.echo_debug("Retrieving project's batch types:")

        try:
            for batch_types in self.get_paginated_batch_types():
                if not batch_types:
                    self.echo_debug("No matching batch types were found.")
                    return

                for batch_type in batch_types:
                    self.echo(get_line(batch_type))

        except client.APIClientError as err:
            self.echo_debug(err)
            if err.status_code == 400:
                self.echo_warning(
                    "There was an error listing project batch types."
                )
                self.echo("The following error was returned:")
                self.echo(err.message)
            elif err.status_code == 404:
                self.echo_warning(
                    "Project {} does not exist or you do not have "
                    "permission required to access it.".format(
                        self.project_id
                    )
                )
            else:
                raise BatchTypesError

    def get_paginated_batch_types(self):
        """Paginate over all batch types for the destination.

        Yields:
            paginated lists of batch types
        """
        more = True
        next_link = None
        while more:
            self.echo_debug("Get batch types page")
            resp = self.get_batch_types(next_link)
            yield resp["results"]
            next_link = resp["meta"]["next"]
            more = next_link is not None

    @backoff.on_exception(
        backoff.expo,
        (requests.exceptions.ConnectionError, requests.exceptions.Timeout),
        max_tries=2,
        max_time=30,
    )
    def get_batch_types(self, next_link=None):
        """Get batch types page."""
        return self.api_client.get_project_batch_types(
            project_id=self.project_id, next_link=next_link
        )
