"""Start shell session for explorer instance subcommand."""

import base64
import os
import signal
import subprocess  # nosec B404 (bandit subprocess import)
import sys
import time
from multiprocessing import Process

from gencove.utils import get_boto_session_refreshable

from ....base import Command
from ....utils import (
    user_has_aws_in_path,
    user_has_session_manager_plugin_in_path,
    user_has_supported_aws_cli,
)
from .....exceptions import ValidationError
from .....models import ExplorerShellSessionCredentials


class ShellSession(Command):
    """Start shell session for explorer instance command executor."""

    def validate(self):
        """Validate start shell sessions"""
        user_has_aws_in_path(raise_exception=True)
        user_has_supported_aws_cli(raise_exception=True)
        user_has_session_manager_plugin_in_path(raise_exception=True)

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

        instance_id = str(explorer_instances.results[0].id)
        self.echo_debug("Requested explorer shell session credentials.")
        credentials = self.api_client.get_explorer_shell_session_credentials(
            instance_id=instance_id
        )

        self.start_ssm_session(credentials, instance_id)

    def start_ssm_session(
        self,
        credentials: ExplorerShellSessionCredentials,
        instance_id: str,
    ):
        """Start SSM session using AWS CLI.

        Args:
            credentials (ExplorerShellSessionCredentials): Credentials
                to send commands to the isntance.
            instance_id (str): Explorer instance id.

        Raises:
            ValidationError: If AWS CLI not available.
        """
        network_activity_background = Process(
            target=self.generate_network_activity,
            args=(credentials, instance_id),
        )
        network_activity_background.start()
        try:
            command = [
                "aws",
                "ssm",
                "start-session",
                "--target",
                credentials.ec2_instance_id,
                "--document-name",
                credentials.shell_session_ssm_document_name,
            ]
            env = os.environ.copy()
            env.update(
                {
                    "AWS_ACCESS_KEY_ID": credentials.access_key,
                    "AWS_SECRET_ACCESS_KEY": credentials.secret_key,
                    "AWS_SESSION_TOKEN": credentials.token,
                    "AWS_DEFAULT_REGION": credentials.region_name,
                    "AWS_REGION": credentials.region_name,
                    "PATH": os.environ["PATH"],
                }
            )
            with subprocess.Popen(  # nosec B603 (execution of untrusted input)
                command,
                env=env,
                stdin=sys.stdin,
                stdout=sys.stdout,
                stderr=sys.stderr,
            ) as process:

                def signal_handler(sig, frame):  # pylint: disable=unused-argument
                    if process.poll() is None:  # Check if the process is still running
                        process.send_signal(sig)

                signal.signal(signal.SIGINT, signal_handler)
                signal.signal(signal.SIGTERM, signal_handler)
                signal.signal(signal.SIGQUIT, signal_handler)
                signal.signal(signal.SIGHUP, signal_handler)

                process.wait()
        finally:
            if network_activity_background.is_alive():
                # Try to gracefully stop the backgroud process
                network_activity_background.terminate()

    def generate_network_activity(
        self,
        credentials: ExplorerShellSessionCredentials,
        instance_id: str,
    ):
        """Spoofs explorer instance network activity by sending random data.
        Runs forever.

        Args:
            credentials (ExplorerShellSessionCredentials): Credentials
                to send commands to the isntance.
            instance_id (str): Explorer instance id.
        """

        def ignore_signal(sig, frame):  # pylint: disable=unused-argument
            self.echo_debug(f"Ignoring SIGNAL in bg process: {sig}")

        signal.signal(signal.SIGINT, ignore_signal)

        def refresh_credentials():
            """Refresh credentials.

            Returns:
                ExplorerShellSessionCredentials: Session credentials.
            """
            return self.api_client.get_explorer_shell_session_credentials(
                instance_id=instance_id
            )

        boto3_session = get_boto_session_refreshable(refresh_credentials)
        ssm_client = boto3_session.client("ssm", region_name=credentials.region_name)
        while True:
            time.sleep(5)
            try:
                random_data = base64.b64encode(os.urandom(50_000)).decode()[:50_000]
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
