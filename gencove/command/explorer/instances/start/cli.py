"""Configure inactivity stop for explorer instances command definition.
"""
import click

from gencove.command.common_cli_options import add_options, common_options
from gencove.constants import Credentials, Optionals

from .main import StartInstances


@click.command("start")
@add_options(common_options)
def start(  # pylint: disable=too-many-arguments
    host,
    email,
    password,
    api_key,
):  # pylint: disable=line-too-long
    """Start instances."""  # noqa: E501
    StartInstances(
        Credentials(email=email, password=password, api_key=api_key),
        Optionals(host=host),
    ).run()
