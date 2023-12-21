"""Start shell session for explorer instance subcommand."""

import base64
import os
import signal
import sys
import time
from multiprocessing import Process
from typing import Callable

from gencove.utils import get_boto_session_refreshable

import sh  # pylint: disable=wrong-import-order

from ....base import Command
from .....exceptions import ValidationError
from .....models import ExplorerShellSessionCredentials


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

        if explorer_instances.results[0].status != "running":
            raise ValidationError(
                "Instance is not running. Cannot start shell session."
            )

        def get_credentials():
            """Return credentials for starting an SSM session/command.

            Returns:
                ExplorerShellSessionCredentials: Credentials.
            """
            self.echo_debug("Requested explorer shell session credentials.")
            return self.api_client.get_explorer_shell_session_credentials(
                instance_id=explorer_instances.results[0].id
            )

        self.start_ssm_session(get_credentials(), get_credentials)

    def start_ssm_session(
        self,
        credentials: ExplorerShellSessionCredentials,
        refresh_credentials: Callable[[], ExplorerShellSessionCredentials],
    ):
        """Start SSM session using AWS CLI.

        Args:
            credentials (ExplorerShellSessionCredentials): Credentials
                to send commands to the isntance.
            refresh_credentials (Callable[[], ExplorerShellSessionCredentials]):
                Refresh method.

        Raises:
            ValidationError: If AWS CLI not available.
        """
        spoof_network_background = Process(
            target=self.spoof_network_activity, args=(credentials, refresh_credentials)
        )
        spoof_network_background.start()
        try:
            command = sh.aws.ssm(  # pylint: disable=no-member
                [
                    "start-session",
                    "--target",
                    credentials.ec2_instance_id,
                    "--document-name",
                    credentials.shell_session_ssm_document_name,
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
                command.signal_group(sig)

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
        finally:
            if spoof_network_background.is_alive():
                # Try to gracefully stop the backgroud process
                spoof_network_background.terminate()

    def spoof_network_activity(
        self,
        credentials: ExplorerShellSessionCredentials,
        refresh_credentials: Callable[[], ExplorerShellSessionCredentials],
    ):
        """Spoofs explorer instance network activity by sending random data.
        Runs forever.

        Args:
            credentials (ExplorerShellSessionCredentials): Credentials
                to send commands to the isntance.
            refresh_credentials (Callable[[], ExplorerShellSessionCredentials]):
                Refresh method.
        """
        boto3_session = get_boto_session_refreshable(refresh_credentials)
        ssm_client = boto3_session.client("ssm")
        while True:
            time.sleep(5)
            try:
                random_data = base64.b64encode(os.urandom(50_000))[:50_000]
                self.echo_debug(
                    f"Spoofing network activity random_data_len={len(random_data)}"
                )
                ssm_client.send_command(
                    InstanceIds=[credentials.ec2_instance_id],
                    DocumentName=credentials.network_activity_ssm_document_name,
                    Parameters={"RandomInputData": [random_data]},
                )
            except Exception as ex:  # pylint: disable=broad-except
                self.echo_debug(
                    f"Error while trying to spoof network activity: {repr(ex)}"
                )
