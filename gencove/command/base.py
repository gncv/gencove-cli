"""Base command layout.

All commands must implement this interface.
"""
from gencove.client import APIClient
from gencove.logger import echo, echo_debug, echo_warning


class Command(object):  # pylint: disable=R0205
    """Base command structure."""

    def __init__(self, credentials, options):
        self.api_client = APIClient(options.host)
        self.is_logged_in = False
        self.credentials = credentials
        self.options = options

    def initialize(self):
        """Put any initializing logic here, such as login."""
        raise NotImplementedError

    def validate(self):
        """Validate that the arguments and initialize were successful."""
        raise NotImplementedError

    def execute(self):
        """Execute command logic."""
        raise NotImplementedError

    def run(self):
        """Run the command.

        No need to override this, unless more customized behaviour is needed.
        """
        self.initialize()
        try:
            self.validate()
        except ValidationError:
            return
        self.execute()

    @staticmethod
    def echo(msg, **kwargs):
        """Output info message."""
        echo(msg, **kwargs)

    @staticmethod
    def echo_warning(msg, **kwargs):
        """Output warning message."""
        echo_warning(msg, **kwargs)

    @staticmethod
    def echo_debug(msg, **kwargs):
        """Output debug message."""
        echo_debug(msg, **kwargs)


class CriticalFailure(Exception):
    """CLI critical error - indicating command exit."""


class ValidationError(Exception):
    """CLI validation error - indicating command input is not valid."""
