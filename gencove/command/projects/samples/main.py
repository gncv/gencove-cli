"""List projects subcommand."""
import backoff

import requests

from tabulate import tabulate

# pylint: disable=wrong-import-order
from gencove.client import APIClientError  # noqa: I100
from gencove.command.base import Command
from gencove.constants import SAMPLE_SORT_BY, SAMPLE_STATUS, SORT_ORDER

from .constants import (
    ALLOWED_SORT_FIELDS_RE,
    ALLOWED_SORT_ORDER_RE,
    ALLOWED_STATUSES_RE,
)
from .exceptions import SamplesError
from .utils import get_line, validate_input


class ListSamples(Command):
    """List sample sheet command executor."""

    def __init__(self, project_id, credentials, options):
        super(ListSamples, self).__init__(credentials, options)
        self.project_id = project_id
        self.sample_status = options.status
        self.search_term = options.search
        self.sort_by = options.sort_by
        self.sort_order = options.sort_order
        self.limit = options.limit

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
        validate_input(
            "sort by", self.sort_by, ALLOWED_SORT_FIELDS_RE, SAMPLE_SORT_BY
        )
        validate_input(
            "sort order", self.sort_order, ALLOWED_SORT_ORDER_RE, SORT_ORDER
        )

    def execute(self):
        self.echo_debug(
            "Retrieving sample sheet: "
            "status={} sort_by={} sort_order={} search_term={}".format(
                self.sample_status,
                self.sort_by,
                self.sort_order,
                self.search_term,
            )
        )
        lines = []
        for samples in self.get_paginated_samples():
            for sample in samples:
                lines.append(get_line(sample))

        if not lines:
            self.echo_debug(
                "Looks like this project doesn't have any samples."
            )
        else:
            self.echo(tabulate(lines, tablefmt="plain"))

    def get_paginated_samples(self):
        """Paginate over all sample sheets for the destination.

        Yields:
            paginated lists of samples
        """
        more = True
        next_link = None
        count = 0
        while more:
            self.echo_debug("Get sample sheet page")
            try:
                resp = self.get_samples(next_link)
                yield resp["results"]
                next_link = resp["meta"]["next"]
                more = next_link is not None
                count += len(resp["results"])
                if self.limit and more:
                    more = count < self.limit
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
            sort_by=self.sort_by,
            sort_order=self.sort_order,
        )
