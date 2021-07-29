"""List BioSamples from BaseSpace project subcommand."""
import backoff

from .utils import get_line
from ....base import Command
from ..... import client


class BioSamplesList(Command):
    """BioSamples list command executor."""

    def __init__(self, basespace_project_id, credentials, options):
        super().__init__(credentials, options)
        self.basespace_project_id = basespace_project_id

    def initialize(self):
        """Initialize basespace biosamples list subcommand."""
        self.login()

    def validate(self):
        """Need to override because it's not implemented in the base class."""
        pass  # pylint: disable=unnecessary-pass

    def execute(self):
        """Make a request to list BioSamples from a BaseSpace project."""
        self.echo_debug(
            "Listing BioSamples from a BaseSpace project {}.".format(
                self.basespace_project_id
            )
        )
        try:
            for biosamples in self.get_paginated_biosamples():
                if not biosamples:
                    self.echo_debug("No BaseSpace BioSamples were found.")
                    return

                for biosample in biosamples:
                    self.echo_data(get_line(biosample))
        except client.APIClientError as err:
            self.echo_error("There was an error listing BioSamples.")
            if err.status_code == 404:
                self.echo_error("No BaseSpace BioSamples found.")
            raise

    def get_paginated_biosamples(self):
        """Paginate over all BioSamples returned.

        Yields:
            paginated lists of BaseSpace BioSamples
        """
        more = True
        next_link = None
        while more:
            self.echo_debug("Get BaseSpace BioSamples page")
            resp = self.get_biosamples(next_link)

            yield resp.results
            next_link = resp.meta.next
            more = next_link is not None

    @backoff.on_exception(
        backoff.expo,
        (client.APIClientTimeout),
        max_tries=2,
        max_time=30,
    )
    def get_biosamples(self, next_link=None):
        """Get BaseSpace BioSamples page."""
        return self.api_client.list_biosamples(
            self.basespace_project_id, next_link
        )
