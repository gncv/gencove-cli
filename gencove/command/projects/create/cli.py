"""Project create shell command definition."""
import click

from gencove.command.common_cli_options import add_options, common_options
from gencove.command.utils import validate_uuid
from gencove.constants import Credentials, Optionals

from .main import CreateProject


@click.command("create")
@click.argument("project_name")
@click.argument("pipeline_capability_id", callback=validate_uuid)
@add_options(common_options)
def create_project(  # pylint: disable=too-many-arguments
    project_name,
    pipeline_capability_id,
    host,
    email,
    password,
    api_key,
):
    """Create a project."""

    CreateProject(
        project_name,
        pipeline_capability_id,
        Credentials(email=email, password=password, api_key=api_key),
        Optionals(host=host),
    ).run()
