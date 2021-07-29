"""List BaseSpace projects subcommand."""
import backoff

from .utils import get_line
from ....base import Command
from ..... import client


class BaseSpaceList(Command):
    """BaseSpace list command executor."""

    def initialize(self):
        """Initialize basespace projects list subcommand."""
        self.login()

    def validate(self):
        """Need to override because it's not implemented in the base class."""
        pass  # pylint: disable=unnecessary-pass

    @backoff.on_exception(
        backoff.expo,
        (client.APIClientTimeout),
        max_tries=2,
        max_time=30,
    )
    def get_basespace_projects(self, next_link=None):
        """Get BaseSpace projects page."""
        return self.api_client.list_basespace_projects(next_link)

    def get_paginated_basespace_projects(self):
        """Paginate over all BaseSpace projects.

        Yields:
            paginated lists of BaseSpace projects
        """
        more = True
        next_link = None
        while more:
            self.echo_debug("Get BaseSpace projects page")
            resp = self.get_basespace_projects(next_link)

            yield resp.results
            next_link = resp.meta.next
            more = next_link is not None

    def execute(self):
        """Make a request to list BaseSpace projects."""
        self.echo_debug("Listing BaseSpace projects.")

        try:
            for basespace_projects in self.get_paginated_basespace_projects():
                if not basespace_projects:
                    self.echo_debug("No BaseSpace projects were found.")
                    return

                for basespace_project in basespace_projects:
                    self.echo_data(get_line(basespace_project))

        except client.APIClientError as err:
            self.echo_error("There was an error listing BaseSpace projects.")
            if err.status_code == 404:
                self.echo_error("No BaseSpace projects found.")
            raise
