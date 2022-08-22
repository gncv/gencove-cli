"""List BaseSpace AutoImport jobs subcommand."""
import backoff

from .utils import get_line
from ....base import Command
from ..... import client


class BaseSpaceAutoImportList(Command):
    """BaseSpace autoimport list command executor."""

    def initialize(self):
        """Initialize basespace-autoimport subcommand."""
        self.login()

    def validate(self):
        """Validate command input."""

    def execute(self):
        """Make a request to list jobs to periodically import Biosamples from
        BaseSpace projects.
        """
        self.echo_debug("List AutoImport jobs.")

        try:
            for basespace_autoimports in self.get_paginated_basespace_autoimports():
                if not basespace_autoimports:
                    self.echo_debug("No BaseSpace autoimport jobs were found.")
                    return
                for basespace_autoimport in basespace_autoimports:
                    self.echo_data(get_line(basespace_autoimport))
        except client.APIClientError:
            self.echo_error(
                "There was an error listing autoimport jobs of BaseSpace projects."
            )
            raise

    def get_paginated_basespace_autoimports(self):
        """Paginate over all BaseSpace autoimports.

        Yields:
            paginated lists of BaseSpace autoimports
        """
        more = True
        next_link = None
        while more:
            self.echo_debug("Get BaseSpace autoimport page")
            resp = self.get_basespace_autoimports(next_link)

            yield resp.results
            next_link = resp.meta.next
            more = next_link is not None

    @backoff.on_exception(
        backoff.expo,
        (client.APIClientTimeout),
        max_tries=2,
        max_time=30,
    )
    def get_basespace_autoimports(self, next_link=None):
        """Get BaseSpace autoimports page."""
        return self.api_client.list_basespace_autoimport_jobs(next_link)
