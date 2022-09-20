"""List file types"""

import backoff

# pylint: disable=wrong-import-order
from gencove import client
from gencove.command.base import Command
from gencove.command.utils import is_valid_uuid
from gencove.exceptions import ValidationError

from .utils import get_line


class ListFileTypes(Command):
    """List file types command executor."""

    # pylint: disable=too-many-arguments
    def __init__(self, project_id, credentials, options):
        super().__init__(credentials, options)
        self.project_id = project_id

    def initialize(self):
        """Initialize list command."""
        self.login()

    def validate(self):
        """Validate command input.

        Raises:
            ValidationError - if something is wrong with command parameters.
        """
        if self.project_id:
            if is_valid_uuid(self.project_id) is False:
                raise ValidationError("Project ID is not valid. Exiting.")

    def execute(self):
        self.echo_debug("Retrieving file types:")

        try:
            for file_types in self.get_file_types():
                sorted_file_types = sorted(file_types, key=lambda ft: ft.key)
                for file_type in sorted_file_types:
                    self.echo_data(get_line(file_type))

        except client.APIClientError as err:
            if err.status_code == 404:
                self.echo_error(f"Project {self.project_id} does not exist.")
            raise

    @backoff.on_exception(
        backoff.expo,
        (client.APIClientTimeout),
        max_tries=2,
        max_time=30,
    )
    def get_file_types(self):
        """Get file types list

        Yields:
            list of file types
        """
        if self.project_id:
            yield self.api_client.get_file_types(project_id=self.project_id).results
        else:
            yield self.api_client.get_file_types().results
