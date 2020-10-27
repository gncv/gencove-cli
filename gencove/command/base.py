"""Base command layout.

All commands must implement this interface.
"""
import click

from gencove.client import APIClient, APIClientError
from gencove.exceptions import ValidationError
from gencove.logger import (
    DEBUG,
    LOG_LEVEL,
    echo_data,
    echo_debug,
    echo_error,
    echo_info,
    echo_warning,
)
from gencove.utils import login, validate_credentials


class Command(object):  # pylint: disable=R0205
    """Base command structure."""

    def __init__(self, credentials, options):
        self.api_client = APIClient(options.host)
        self.is_logged_in = False
        self.credentials = credentials
        self.options = options
        self.is_credentials_valid = validate_credentials(credentials)

    def initialize(self):
        """Put any initializing logic here, such as login."""
        raise NotImplementedError

    def validate(self):
        """Validate that the arguments and initialize were successful."""
        raise NotImplementedError

    def execute(self):
        """Execute command logic."""
        raise NotImplementedError

    def validate_login_success(self):
        """Check if login succeeded."""
        if not self.is_logged_in:
            raise ValidationError(
                "Please check your credentials and try again"
            )

    def run(self):
        """Run the command.

        No need to override this, unless more customized behaviour is needed.
        """
        try:
            self.initialize()
            self.validate()
            self.validate_login_success()
            self.execute()
        except ValidationError as err:
            self.echo_error(err.message)
            raise click.Abort()
        except APIClientError as err:
            self.echo_error(err.message)
            if LOG_LEVEL == DEBUG:
                raise err
            raise click.Abort()

    def login(self):
        """Login current user."""
        if not self.is_credentials_valid:
            return False
        self.is_logged_in = login(self.api_client, self.credentials)
        return self.is_logged_in

    @staticmethod
    def echo_data(msg, **kwargs):
        """Output data message."""
        echo_data(msg, **kwargs)

    @staticmethod
    def echo_info(msg, **kwargs):
        """Output info message."""
        echo_info(msg, **kwargs)

    @staticmethod
    def echo_warning(msg, **kwargs):
        """Output warning message."""
        echo_warning(msg, **kwargs)

    @staticmethod
    def echo_error(msg, **kwargs):
        """Output error message."""
        echo_error(msg, **kwargs)

    @staticmethod
    def echo_debug(msg, **kwargs):
        """Output debug message."""
        echo_debug(msg, **kwargs)
