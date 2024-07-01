"""Configure explorer data restore definition."""
import click

from gencove.command.common_cli_options import add_options, common_options
from gencove.constants import Credentials, Optionals

from .main import Restore


@click.command(
    "restore",
    help="Restore archived data in Explorer object storage",
    context_settings=dict(
        ignore_unknown_options=True,
        allow_extra_args=True,
    ),
)
@click.argument("path", type=click.Path(), default="e://")
@click.option(
    "--days", default=30, help="Days that the restored data will be available for."
)
@click.option(
    "--tier",
    default="Bulk",
    help=(
        "When restoring an archived object, "
        "you can specify one of the following data access tier options: "
        "Expedited, Standard, Bulk."
    ),
)
@click.pass_context
@add_options(common_options)
def restore(  # pylint: disable=too-many-arguments,invalid-name
    ctx,
    path,
    days,
    tier,
    host,
    email,
    password,
    api_key,
):  # pylint: disable=line-too-long
    """Restore archived objects."""  # noqa: E501
    Restore(
        ctx,
        path,
        days,
        tier,
        Credentials(email=email, password=password, api_key=api_key),
        Optionals(host=host),
    ).run()
