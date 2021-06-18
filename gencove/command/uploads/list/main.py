"""List uploads subcommand."""
import backoff

# pylint: disable=wrong-import-order
from gencove.client import APIClientError, APIClientTimeout  # noqa: I100
from gencove.command.base import Command

from .utils import get_line


class ListSampleSheet(Command):
    """List sample sheet command executor."""

    def __init__(self, credentials, options):
        super().__init__(credentials, options)
        self.status = options.status
        self.gncv_path = options.search

    def initialize(self):
        """Initialize list subcommand."""
        self.login()

    def validate(self):
        """Validate command input."""
        pass  # pylint: disable=unnecessary-pass

    def execute(self):
        self.echo_debug(
            "Retrieving sample sheet: "
            "status={} search_term={}".format(self.status, self.gncv_path)
        )
        try:
            for uploads in self.get_paginated_sample_sheet():
                if not uploads:
                    self.echo_debug("No matching uploads found.")
                    return

                for upload in uploads:
                    self.echo_data(get_line(upload))
        except APIClientError as err:
            if err.status_code == 404:
                self.echo_error("Uploads do not exist.")
            raise

    def get_paginated_sample_sheet(self):
        """Paginate over all sample sheet pages.

        Yields:
            paginated lists of uploads
        """
        more = True
        next_link = None
        while more:
            self.echo_debug("Get sample sheet page")
            resp = self.get_sample_sheet(next_link)
            yield resp.results
            next_link = resp.meta.next
            more = next_link is not None

    @backoff.on_exception(
        backoff.expo,
        (APIClientTimeout),
        max_tries=5,
        max_time=30,
    )
    def get_sample_sheet(self, next_link=None):
        """Get sample sheet page."""
        return self.api_client.get_sample_sheet(
            gncv_path=self.gncv_path,
            assigned_status=self.status,
            next_link=next_link,
        )
