"""List projects subcommand."""
import backoff

import requests

# pylint: disable=wrong-import-order
from gencove.client import APIClientError  # noqa: I100
from gencove.command.base import Command
from gencove.constants import SAMPLE_STATUS

from .constants import ALLOWED_STATUSES_RE
from .exceptions import SamplesError
from .utils import get_line
from ...utils import validate_input


class ListSamples(Command):
    """List samples command executor."""

    def __init__(self, project_id, credentials, options):
        super(ListSamples, self).__init__(credentials, options)
        self.project_id = project_id
        self.sample_status = options.status
        self.search_term = options.search

    def initialize(self):
        """Initialize list subcommand."""
        self.login()

    def validate(self):
        """Validate command input."""
        validate_input(
            "sample status",
            self.sample_status,
            ALLOWED_STATUSES_RE,
            SAMPLE_STATUS,
        )

    def execute(self):
        self.echo_debug(
            "Retrieving sample sheet: "
            "status={} search_term={}".format(
                self.sample_status, self.search_term
            )
        )
        for samples in self.get_paginated_samples():
            if not samples:
                self.echo_debug("No matching samples were found.")
                return

            for sample in samples:
                self.echo(get_line(sample))

    def get_paginated_samples(self):
        """Paginate over all sample sheets for the destination.

        Yields:
            paginated lists of samples
        """
        more = True
        next_link = None
        while more:
            self.echo_debug("Get sample sheet page")
            try:
                resp = self.get_samples(next_link)
                yield resp["results"]
                next_link = resp["meta"]["next"]
                more = next_link is not None
            except APIClientError as err:
                self.echo_debug(err)
                raise SamplesError

    @backoff.on_exception(
        backoff.expo,
        (requests.exceptions.ConnectionError, requests.exceptions.Timeout),
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
        )
