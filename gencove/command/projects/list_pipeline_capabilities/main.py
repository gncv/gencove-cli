"""List pipeline capabilities subcommand."""

import backoff

from gencove import client
from gencove.command.base import Command

from .utils import get_line


class ListPipelineCapabilities(Command):
    """List pipeline capabilities command executor."""

    def __init__(self, pipeline_id, credentials, options):
        super().__init__(credentials, options)
        self.pipeline_id = pipeline_id

    def initialize(self):
        """Initialize list subcommand."""
        self.login()

    def validate(self):
        """Validate command input."""

    def execute(self):
        self.echo_debug("Retrieving possible pipeline capabilities:")

        try:
            pipeline_capabilities = self.get_pipeline_capabilities()
            for pipeline_capability in pipeline_capabilities.capabilities:
                self.echo_data(get_line(pipeline_capability))
        except client.APIClientError as err:
            self.echo_debug(err)
            if err.status_code == 400:
                self.echo_warning("There was an error listing pipeline capabilities.")
                self.echo_info("The following error was returned:")
                self.echo_info(err.message)
            elif err.status_code == 404:
                self.echo_error(f"Pipeline {self.pipeline_id} does not exist.")
            raise

    @backoff.on_exception(
        backoff.expo,
        (client.APIClientTimeout),
        max_tries=2,
        max_time=30,
    )
    def get_pipeline_capabilities(self):
        """Get pipeline capabilities page."""
        return self.api_client.get_pipeline_capabilities_for_pipeline(
            pipeline_id=self.pipeline_id,
        )
