"""Project pipelines list shell command definition."""
import click

from gencove.command.common_cli_options import add_options, common_options
from gencove.constants import Credentials, Optionals

from .main import ListPipelines


@click.command("list-pipelines")
@add_options(common_options)
def list_project_pipelines(host, email, password, api_key):
    """List pipelines that are available when creating a project."""
    ListPipelines(
        Credentials(email=email, password=password, api_key=api_key),
        Optionals(host=host),
    ).run()
