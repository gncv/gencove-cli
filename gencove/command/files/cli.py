"""Commands to be executed from command line."""
import click

from gencove.command.common_cli_options import add_options, common_options
from gencove.constants import Credentials, Optionals

from .main import ListFileTypes


@click.command("file-types")
@click.argument("project_id", required=False)
@add_options(common_options)
def file_types(project_id, host, email, password, api_key):
    """List file types in Gencove's system.

    PROJECT_ID (optional): List file types for a particular project

    Args:
        project_id (UUID, optional): ID of a project to list file types for.
    """
    ListFileTypes(
        project_id,
        Credentials(email=email, password=password, api_key=api_key),
        Optionals(host=host),
    ).run()
