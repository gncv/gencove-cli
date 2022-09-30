"""List projects subcommand."""
import backoff

# pylint: disable=wrong-import-order
from gencove.client import APIClientError, APIClientTimeout  # noqa: I100
from gencove.command.base import Command

from .utils import get_line


class ListSamples(Command):
    """List samples command executor."""

    def __init__(self, project_id, credentials, options):
        super().__init__(credentials, options)
        self.project_id = project_id
        self.sample_status = options.status
        self.sample_archive_status = options.archive_status
        self.search_term = options.search

    def initialize(self):
        """Initialize list subcommand."""
        self.login()

    def validate(self):
        """Validate command input."""

    def execute(self):
        self.echo_debug(
            "Retrieving sample sheet: "
            f"status={self.sample_status} "
            f"archive_status={self.sample_archive_status} "
            f"search_term={self.search_term}"
        )
        try:
            for samples in self.get_paginated_samples():
                if not samples:
                    self.echo_debug("No matching samples were found.")
                    return

                for sample in samples:
                    self.echo_data(get_line(sample))
        except APIClientError as err:
            if err.status_code == 404:
                self.echo_error(f"Project {self.project_id} does not exist.")
            raise

    def get_paginated_samples(self):
        """Paginate over all sample sheets for the destination.

        Yields:
            paginated lists of samples
        """
        more = True
        next_link = None
        while more:
            self.echo_debug("Get sample sheet page")
            resp = self.get_samples(next_link)
            yield resp.results
            next_link = resp.meta.next
            more = next_link is not None

    @backoff.on_exception(
        backoff.expo,
        (APIClientTimeout),
        max_tries=2,
        max_time=30,
    )
    def get_samples(self, next_link=None):
        """Get sample sheet page."""
        return self.api_client.get_project_samples(
            project_id=self.project_id,
            next_link=next_link,
            search=self.search_term,
            sample_status=self.sample_status,
            sample_archive_status=self.sample_archive_status,
        )
