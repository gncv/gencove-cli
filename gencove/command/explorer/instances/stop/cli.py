"""Configure inactivity stop for explorer instances command definition.
"""
import click

from gencove.command.common_cli_options import add_options, common_options
from gencove.constants import Credentials, Optionals

from .main import StopInstances


@click.command("stop")
@add_options(common_options)
def stop(  # pylint: disable=too-many-arguments
    host,
    email,
    password,
    api_key,
):  # pylint: disable=line-too-long
    """Stop instances."""  # noqa: E501
    StopInstances(
        Credentials(email=email, password=password, api_key=api_key),
        Optionals(host=host),
    ).run()
