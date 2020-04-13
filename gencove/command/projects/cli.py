"""Commands to be executed from command line."""
# pylint: disable=C0330,R0913
import click

from gencove.command.common_cli_options import add_options, common_options
from gencove.constants import (
    Credentials,
    Optionals,
    SAMPLE_SORT_BY,
    SAMPLE_STATUS,
    SORT_ORDER,
)

from .list.main import List
from .samples.constants import SamplesOptions
from .samples.main import ListSamples


@click.group()
def projects():
    """Project managements commands."""


@projects.command("list")
@add_options(common_options)
def list_projects(host, email, password, api_key):
    """List your projects."""
    List(Credentials(email, password, api_key), Optionals(host)).run()


@projects.command("list-samples")
@click.argument("project_id")
@click.option("--search", help="Gencove sample ID or client ID")
@click.option(
    "--status",
    help="Get samples with specific status",
    type=click.Choice(SAMPLE_STATUS._asdict().values()),
    default=SAMPLE_STATUS.all,
)
@click.option(
    "--sort-by",
    help="Sort samples by specific field",
    type=click.Choice(SAMPLE_SORT_BY._asdict().values()),
    default=SAMPLE_SORT_BY.modified,
)
@click.option(
    "--sort-order",
    help="Sort samples in ascending or descending order",
    type=click.Choice(SORT_ORDER._asdict().values()),
    default=SORT_ORDER.desc,
)
@click.option(
    "--limit",
    help="Limit number of returned samples. "
    "If not provided, all samples will be returned.",
)
@add_options(common_options)
def list_project_samples(
    project_id,
    search,
    status,
    sort_by,
    sort_order,
    limit,
    host,
    email,
    password,
    api_key,
):
    """List samples in a project."""
    ListSamples(
        project_id,
        Credentials(email, password, api_key),
        SamplesOptions(host, status, search, sort_by, sort_order, limit),
    ).run()
