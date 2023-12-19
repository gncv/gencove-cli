"""Start shell session for explorer instance subcommand."""

import signal
import sys

import sh


from ....base import Command
from .....exceptions import ValidationError


class ShellSession(Command):
    """Start shell session for explorer instance command executor."""

    def validate(self):
        """Validate start shell sessions"""

    def initialize(self):
        """Initialize shell subcommand."""
        self.login()

    def execute(self):
        """Make a request to get shell session credentials."""

        explorer_instances = self.api_client.get_explorer_instances()
        self.echo_debug(f"Found {len(explorer_instances.results)} explorer instances.")

        if len(explorer_instances.results) != 1:
            raise ValidationError(
                "Command not supported. Download the latest version of the Gencove CLI."
            )

        credentials = self.api_client.get_explorer_shell_session_credentials(
            instance_id=explorer_instances.results[0].id
        )
        self.echo_debug("Requested explorer shell session credentials.")

        try:
            command = sh.aws.ssm(  # pylint: disable=no-member
                [
                    "start-session",
                    "--target",
                    credentials.ec2_instance_id,
                    "--document-name",
                    credentials.ssm_document_name,
                ],
                _env={
                    "AWS_ACCESS_KEY_ID": credentials.access_key,
                    "AWS_SECRET_ACCESS_KEY": credentials.secret_key,
                    "AWS_SESSION_TOKEN": credentials.token,
                },
                _in=sys.stdin,
                _out=sys.stdout,
                _bg=True,
            )

            def signal_handler(sig, frame):  # pylint: disable=unused-argument
                command.signal(sig)

            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)
            signal.signal(signal.SIGQUIT, signal_handler)
            signal.signal(signal.SIGHUP, signal_handler)

            command.wait()
        except sh.CommandNotFound as ex:
            raise ValidationError(
                "AWS CLI not available. Please follow installation instructions at"
                "https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-install.html"
            ) from ex
