"""Commands to be executed from command line."""
import click

from gencove.command.common_cli_options import add_options, common_options
from gencove.constants import Credentials, Optionals

from .main import ListFileTypes


@click.command("file-types")
@click.option("--project-id", required=False, help="Gencove project ID")
@add_options(common_options)
def list_file_types(project_id, host, email, password, api_key):
    """List file types in Gencove's system.

    PROJECT_ID (optional): List file types for a particular project

    Args:
        project_id (UUID, optional): project id in Gencove's system.
    """
    ListFileTypes(
        project_id,
        Credentials(email=email, password=password, api_key=api_key),
        Optionals(host=host),
    ).run()
