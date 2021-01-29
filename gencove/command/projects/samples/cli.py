"""Samples list shell command definition."""
import click

from gencove.command.common_cli_options import add_options, common_options
from gencove.constants import (
    Credentials,
    SAMPLE_ARCHIVE_STATUS,
    SAMPLE_STATUS,
)

from .constants import SamplesOptions
from .main import ListSamples


@click.command("list-samples")
@click.argument("project_id")
@click.option(
    "--search", help="Gencove sample ID, client ID or metadata substring"
)
@click.option(
    "--status",
    help="Get samples with specific status",
    type=click.Choice(SAMPLE_STATUS._asdict().values()),
    default=SAMPLE_STATUS.all,
)
@click.option(
    "--archive-status",
    help="Get samples with specific archive status",
    type=click.Choice(SAMPLE_ARCHIVE_STATUS._asdict().values()),
    default=SAMPLE_ARCHIVE_STATUS.all,
)
@add_options(common_options)
def list_project_samples(  # pylint: disable=E0012,C0330,R0913
    project_id, search, status, archive_status, host, email, password, api_key
):
    """List samples in a project."""
    ListSamples(
        project_id,
        Credentials(email, password, api_key),
        SamplesOptions(host, status, archive_status, search),
    ).run()
