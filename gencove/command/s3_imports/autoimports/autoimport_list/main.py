"""List S3 AutoImport jobs subcommand."""
import backoff

from .utils import get_line
from ....base import Command
from ..... import client


class S3AutoImportList(Command):
    """S3 autoimport list command executor."""

    def initialize(self):
        """Initialize s3-autoimport subcommand."""
        self.login()

    def validate(self):
        """Validate command input."""

    def execute(self):
        """Make a request to list jobs to periodically import from S3 URI."""
        self.echo_debug("List AutoImport jobs.")

        try:
            for s3_autoimports in self.get_paginated_s3_autoimports():
                if not s3_autoimports:
                    self.echo_debug("No S3 autoimport jobs were found.")
                    return
                for s3_autoimport in s3_autoimports:
                    self.echo_data(get_line(s3_autoimport))
        except client.APIClientError:
            self.echo_error("There was an error listing S3 autoimport jobs.")
            raise

    def get_paginated_s3_autoimports(self):
        """Paginate over all S3 autoimports.

        Yields:
            paginated lists of S3 autoimports
        """
        more = True
        next_link = None
        while more:
            self.echo_debug("Get S3 autoimport page")
            resp = self.get_s3_autoimports(next_link)

            yield resp.results
            next_link = resp.meta.next
            more = next_link is not None

    @backoff.on_exception(
        backoff.expo,
        (client.APIClientTimeout),
        max_tries=2,
        max_time=30,
    )
    def get_s3_autoimports(self, next_link=None):
        """Get S3 autoimports page."""
        return self.api_client.list_s3_autoimport_jobs(next_link)
