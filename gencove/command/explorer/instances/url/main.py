"""Configure inactivity stop for explorer instances subcommand."""

from ....base import Command
from .....exceptions import ValidationError


class GetInstanceURL(Command):
    """Get explorer instance URL command executor."""

    def __init__(self, expiration_seconds, credentials, options):
        super().__init__(credentials, options)
        self.expiration_seconds = expiration_seconds

    def validate(self):
        """Validate get URL"""

    def initialize(self):
        """Initialize get URL subcommand."""
        self.login()

    def execute(self):
        """Make a request to get explorer instance URL."""
        self.echo_debug("Get explorer instance URL.")

        explorer_instances = self.api_client.get_explorer_instances()
        self.echo_debug(f"Found {len(explorer_instances.results)} explorer instances.")

        if len(explorer_instances.results) != 1:
            raise ValidationError(
                "Command not supported. Download the latest version of the Gencove CLI."
            )

        if explorer_instances.results[0].status != "running":
            raise ValidationError(
                "Instance is not running. Cannot retrieve access URL."
            )

        instance_id = str(explorer_instances.results[0].id)
        self.echo_info("Request to generate explorer access URL accepted.")
        url = self.api_client.get_explorer_access_url(
            instance_id=instance_id,
            access_token_expiration=self.expiration_seconds,
        )
        self.echo_info(
            f"Explorer access URL "
            f"(valid for {self.expiration_seconds} seconds):\n{url.url}"
        )
