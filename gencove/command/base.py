"""Base command layout.

All commands must implement this interface.
"""
import contextlib
import os
import tempfile
import traceback
from functools import wraps

import click

from gencove.client import APIClient, APIClientError
from gencove.exceptions import MaintenanceError, ValidationError
from gencove.logger import (
    DEBUG,
    LOG_LEVEL,
    dump_debug_log,
    echo_data,
    echo_debug,
    echo_error,
    echo_info,
    echo_warning,
)
from gencove.utils import login, validate_credentials

AWS_PROFILE = "AWS_PROFILE"
AWS_CONFIG_FILE = "AWS_CONFIG_FILE"
AWS_SHARED_CREDENTIALS_FILE = "AWS_SHARED_CREDENTIALS_FILE"
env_var_save_restore = [
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "AWS_SESSION_TOKEN",
    "AWS_SECURITY_TOKEN",
    "AWS_DEFAULT_REGION",
    "AWS_DEFAULT_PROFILE",
    "AWS_CA_BUNDLE",
    AWS_SHARED_CREDENTIALS_FILE,
    AWS_CONFIG_FILE,
    AWS_PROFILE,
]

PROFILE_NAME = "gencove-cli-profile"


@contextlib.contextmanager
def aws_cli_credentials():
    """Hides all AWS environment variables, creates new AWS_PROFILE and
    associated config files. During context manager cleanup, restores all
    the environment variables and deletes the temporary files.
    """
    # Saving initial state of env variables
    env_var_saved = {}
    for env_var in env_var_save_restore:
        env_var_saved[env_var] = os.getenv(env_var, default=None)
        if env_var_saved[env_var] is not None:
            del os.environ[env_var]

    # Set AWS_PROFILE
    os.environ[AWS_PROFILE] = PROFILE_NAME

    # Set AWS_CONFIG_FILE
    with tempfile.NamedTemporaryFile(delete=False) as config_file:
        config_file.write(b"[profile " + PROFILE_NAME.encode("utf") + b"]\n")
        aws_config_file = config_file.name
        os.environ[AWS_CONFIG_FILE] = aws_config_file

    # Set AWS_SHARED_CREDENTIALS_FILE
    with tempfile.NamedTemporaryFile(delete=False) as credentials_file:
        credentials_file.write(b"[profile " + PROFILE_NAME.encode("utf") + b"]\n")
        aws_shared_credentials_file = credentials_file.name
        os.environ[AWS_SHARED_CREDENTIALS_FILE] = aws_shared_credentials_file

    try:
        yield
    finally:
        # Remove all modified env variables
        for env_var in env_var_save_restore:
            if env_var in os.environ:
                del os.environ[env_var]

        # Restore original env variables
        for env_var, env_var_value in env_var_saved.items():
            if env_var_value is not None:
                os.environ[env_var] = env_var_value

        # Remove tmp files
        os.remove(aws_config_file)
        os.remove(aws_shared_credentials_file)


def aws_cli_decorator(wrapped_func):
    """Executes a function inside the aws_cli_credentials context manager.

    Args:
        wrapped_func (callable): Function to call.
    """

    @wraps(wrapped_func)
    def wrapper(*args, **kwargs):
        with aws_cli_credentials():
            return wrapped_func(*args, **kwargs)

    return wrapper


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
            raise ValidationError("Please check your credentials and try again")

    @aws_cli_decorator
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
            dump_debug_log()
            raise click.Abort()
        except MaintenanceError as err:
            self.echo_error(err.message)
            self.echo_error(f"ETA is {err.eta}")
            dump_debug_log()
            raise click.Abort()
        except APIClientError as err:
            if err.status_code == 403:
                self.echo_error(
                    "You do not have the sufficient permission "
                    "level required to perform this operation."
                )
            self.echo_error(err.message)
            dump_debug_log()
            if LOG_LEVEL == DEBUG:
                raise err
            raise click.Abort()
        except Exception as err:
            self.echo_error(traceback.format_exc())
            dump_debug_log()
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
