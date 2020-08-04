"""Project batch types list shell command definition."""
import click

from gencove.command.common_cli_options import add_options, common_options
from gencove.constants import Credentials, Optionals

from .main import ListBatchTypes


@click.command("list-batch-types")
@click.argument("project_id")
@add_options(common_options)
def list_project_batch_types(project_id, host, email, password, api_key):
    """List batch types that are available for a project.
    """
    ListBatchTypes(
        project_id, Credentials(email, password, api_key), Optionals(host)
    ).run()
