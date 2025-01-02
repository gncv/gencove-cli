"""Configure explorer data cp definition."""
import click

from gencove.command.common_cli_options import add_options, common_options
from gencove.constants import Credentials, Optionals

from .main import Copy


@click.command(
    "cp",
    help="Copy data to/from Explorer object storage",
    context_settings=dict(
        ignore_unknown_options=True,
        allow_extra_args=True,
    ),
)
@click.argument(
    "source",
    type=click.Path(),
)
@click.argument(
    "destination",
    type=click.Path(),
)
@click.option(
    "--auto-expire",
    help="If this flag is set the object will be expired after 7 days",
    is_flag=True,
    default=False,
    show_default=True,
)
@click.option(
    "--no-auto-archive",
    help=(
        "By default objects are archived after 7 days, if this flag is "
        "set the objects will not be archived"
    ),
    is_flag=True,
    default=False,
    show_default=True,
)
@click.pass_context
@add_options(common_options)
def cp(  # pylint: disable=too-many-arguments,invalid-name
    ctx,
    source,
    destination,
    auto_expire,
    no_auto_archive,
    host,
    email,
    password,
    api_key,
):  # pylint: disable=line-too-long
    """Start instances."""  # noqa: E501
    Copy(
        ctx,
        source,
        destination,
        auto_expire,
        no_auto_archive,
        Credentials(email=email, password=password, api_key=api_key),
        Optionals(host=host),
    ).run()
