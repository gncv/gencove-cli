"""Base command layout.

All commands must implement this interface.
"""
from gencove.client import APIClient, APIClientError
from gencove.logger import DEBUG, LOG_LEVEL, echo, echo_debug, echo_warning
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
            self.echo_debug(repr(err))
        except APIClientError as err:
            echo(err.message, err=True)
            if LOG_LEVEL == DEBUG:
                raise err

    def login(self):
        """Login current user."""
        if not self.is_credentials_valid:
            return False
        self.is_logged_in = login(self.api_client, self.credentials)
        return self.is_logged_in

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
