"""Configure explorer data archive definition."""
import click

from gencove.command.common_cli_options import add_options, common_options
from gencove.constants import Credentials, Optionals

from .main import Archive


@click.command(
    "archive",
    help="Archive data in Explorer object storage",
    context_settings=dict(
        ignore_unknown_options=True,
        allow_extra_args=True,
    ),
)
@click.argument("path", type=click.Path())
@click.pass_context
@add_options(common_options)
def archive(  # pylint: disable=too-many-arguments,invalid-name
    ctx,
    path,
    host,
    email,
    password,
    api_key,
):  # pylint: disable=line-too-long
    """Archive objects."""  # noqa: E501
    Archive(
        ctx,
        path,
        Credentials(email=email, password=password, api_key=api_key),
        Optionals(host=host),
    ).run()
