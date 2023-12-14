"""Configure inactivity stop for explorer instances command definition.
"""
import click

from gencove.command.common_cli_options import add_options, common_options
from gencove.constants import Credentials, Optionals

from .main import List


@click.command(
    "ls",
    help="List data in Explorer object storage",
    context_settings=dict(
        ignore_unknown_options=True,
        allow_extra_args=True,
    ),
)
@click.argument("path", type=click.Path(), default="e://")
@click.pass_context
@add_options(common_options)
def ls(  # pylint: disable=too-many-arguments,invalid-name
    ctx,
    path,
    host,
    email,
    password,
    api_key,
):  # pylint: disable=line-too-long
    """Start instances."""  # noqa: E501
    List(
        ctx,
        path,
        Credentials(email=email, password=password, api_key=api_key),
        Optionals(host=host),
    ).run()
