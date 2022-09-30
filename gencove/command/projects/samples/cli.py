"""Samples list shell command definition."""
import click

from gencove.command.common_cli_options import add_options, common_options
from gencove.command.utils import validate_uuid
from gencove.constants import (
    Credentials,
    SampleArchiveStatus,
    SampleStatus,
)
from gencove.utils import enum_as_dict

from .constants import SamplesOptions
from .main import ListSamples


@click.command("list-samples")
@click.argument("project_id", callback=validate_uuid)
@click.option("--search", help="Gencove sample ID, client ID or metadata substring")
@click.option(
    "--status",
    help="Get samples with specific status",
    type=click.Choice(enum_as_dict(SampleStatus).values()),
    default=SampleStatus.ALL.value,
)
@click.option(
    "--archive-status",
    help="Get samples with specific archive status",
    type=click.Choice(enum_as_dict(SampleArchiveStatus).values()),
    default=SampleArchiveStatus.ALL.value,
)
@add_options(common_options)
def list_project_samples(  # pylint: disable=E0012,C0330,R0913
    project_id, search, status, archive_status, host, email, password, api_key
):
    """List samples in a project."""
    ListSamples(
        project_id,
        Credentials(email=email, password=password, api_key=api_key),
        SamplesOptions(
            host=host,
            status=status,
            archive_status=archive_status,
            search=search,
        ),
    ).run()
