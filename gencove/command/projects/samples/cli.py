"""Samples list shell command definition."""
import click

from gencove.command.common_cli_options import add_options, common_options
from gencove.constants import Credentials, SAMPLE_STATUS

from .constants import SamplesOptions
from .main import ListSamples


@click.command("list-samples")
@click.argument("project_id")
@click.option("--search", help="Gencove sample ID or client ID")
@click.option(
    "--status",
    help="Get samples with specific status",
    type=click.Choice(SAMPLE_STATUS._asdict().values()),
    default=SAMPLE_STATUS.all,
)
@add_options(common_options)
def list_project_samples(  # pylint: disable=C0330,R0913
    project_id, search, status, host, email, password, api_key
):
    """List samples in a project."""
    ListSamples(
        project_id,
        Credentials(email, password, api_key),
        SamplesOptions(host, status, search),
    ).run()
