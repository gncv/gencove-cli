"""Configure explorer data rm definition."""
import click

from gencove.command.common_cli_options import add_options, common_options
from gencove.constants import Credentials, Optionals

from .main import Remove


@click.command(
    "rm",
    help="Remove data from Explorer object storage",
    context_settings=dict(
        ignore_unknown_options=True,
        allow_extra_args=True,
    ),
)
@click.argument(
    "path",
    type=click.Path(),
)
@click.pass_context
@add_options(common_options)
def rm(  # pylint: disable=too-many-arguments,invalid-name
    ctx,
    path,
    host,
    email,
    password,
    api_key,
):  # pylint: disable=line-too-long
    """Start instances."""  # noqa: E501
    Remove(
        ctx,
        path,
        Credentials(email=email, password=password, api_key=api_key),
        Optionals(host=host),
    ).run()
