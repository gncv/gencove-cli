"""Samples list shell command definition."""
import click

from gencove.command.common_cli_options import add_options, common_options
from gencove.constants import Credentials, SampleAssignmentStatus
from gencove.utils import enum_as_dict

from .constants import UploadsOptions
from .main import ListSampleSheet


@click.command("list")
@click.option("--search", help="Filter uploads by gncv path")
@click.option(
    "--status",
    help="Filter uploads by status of assignment",
    type=click.Choice(enum_as_dict(SampleAssignmentStatus).values()),
    default=SampleAssignmentStatus.ALL.value,
)
@add_options(common_options)
def list_uploads(  # pylint: disable=E0012,C0330,R0913
    search, status, host, email, password, api_key
):
    """List user uploads."""
    ListSampleSheet(
        Credentials(email=email, password=password, api_key=api_key),
        UploadsOptions(host=host, status=status, search=search),
    ).run()
