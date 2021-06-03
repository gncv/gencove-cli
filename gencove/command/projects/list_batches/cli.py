"""Project batches list shell command definition."""
import click

from gencove.command.common_cli_options import add_options, common_options
from gencove.constants import Credentials, Optionals

from .main import ListBatches


@click.command("list-batches")
@click.argument("project_id")
@add_options(common_options)
def list_project_batches(project_id, host, email, password, api_key):
    """List batches that are available for a project."""
    ListBatches(
        project_id,
        Credentials(email=email, password=password, api_key=api_key),
        Optionals(host=host),
    ).run()
