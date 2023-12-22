"""Explorer shell session command definition.
"""
import click

from gencove.command.common_cli_options import add_options, common_options
from gencove.constants import Credentials, Optionals

from .main import ShellSession


@click.command("shell")
@add_options(common_options)
def shell(  # pylint: disable=too-many-arguments
    host,
    email,
    password,
    api_key,
):  # pylint: disable=line-too-long
    """Start explorer shell session."""  # noqa: E501
    ShellSession(
        Credentials(email=email, password=password, api_key=api_key),
        Optionals(host=host),
    ).run()
