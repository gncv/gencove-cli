"""List project's pipelines subcommand."""

import backoff

from gencove import client
from gencove.command.base import Command

from .utils import get_line


class ListPipelines(Command):
    """List pipelines command executor."""

    def initialize(self):
        """Initialize list subcommand."""
        self.login()

    def validate(self):
        """Validate command input."""

    def execute(self):
        self.echo_debug("Retrieving possible pipelines:")

        try:
            for pipelines in self.get_paginated_pipelines():
                if not pipelines:
                    self.echo_debug("No matching pipelines were found.")
                    return

                for pipeline in pipelines:
                    self.echo_data(get_line(pipeline))
        except client.APIClientError as err:
            self.echo_debug(err)
            if err.status_code == 400:
                self.echo_warning("There was an error listing pipelines.")
                self.echo_info("The following error was returned:")
                self.echo_info(err.message)
            else:
                raise

    def get_paginated_pipelines(self):
        """Paginate over all pipelines for the destination.

        Yields:
            paginated lists of pipelines
        """
        more = True
        next_link = None
        while more:
            self.echo_debug("Get pipelines page")
            resp = self.get_pipelines(next_link)
            yield resp.results
            next_link = resp.meta.next
            more = next_link is not None

    @backoff.on_exception(
        backoff.expo,
        (client.APIClientTimeout),
        max_tries=2,
        max_time=30,
    )
    def get_pipelines(self, next_link=None):
        """Get pipelines page."""
        return self.api_client.get_pipelines(next_link=next_link)
