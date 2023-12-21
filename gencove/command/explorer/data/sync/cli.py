"""Configure explorer data sync definition."""
import click

from gencove.command.common_cli_options import add_options, common_options
from gencove.constants import Credentials, Optionals

from .main import Sync


@click.command(
    "sync",
    help="Sync directories to/from Explorer object storage",
    context_settings=dict(
        ignore_unknown_options=True,
        allow_extra_args=True,
    ),
)
@click.argument(
    "source",
    type=click.Path(file_okay=False, dir_okay=True),
)
@click.argument(
    "destination",
    type=click.Path(file_okay=False, dir_okay=True),
)
@click.pass_context
@add_options(common_options)
def sync(  # pylint: disable=too-many-arguments,invalid-name
    ctx,
    source,
    destination,
    host,
    email,
    password,
    api_key,
):  # pylint: disable=line-too-long
    """Start instances."""  # noqa: E501
    Sync(
        ctx,
        source,
        destination,
        Credentials(email=email, password=password, api_key=api_key),
        Optionals(host=host),
    ).run()
