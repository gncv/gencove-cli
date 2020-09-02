"""Samples list shell command definition."""
import click

from gencove.command.common_cli_options import add_options, common_options
from gencove.constants import Credentials, SAMPLE_ASSIGNMENT_STATUS

from .constants import UploadsOptions
from .main import ListSampleSheet


@click.command("list")
@click.option("--search", help="Filter uploads by gncv path")
@click.option(
    "--status",
    help="Filter uploads by status of assignment",
    type=click.Choice(SAMPLE_ASSIGNMENT_STATUS._asdict().values()),
    default=SAMPLE_ASSIGNMENT_STATUS.all,
)
@add_options(common_options)
def list_uploads(  # pylint: disable=E0012,C0330,R0913
    search, status, host, email, password, api_key
):
    """List user uploads."""
    ListSampleSheet(
        Credentials(email, password, api_key),
        UploadsOptions(host, status, search),
    ).run()
