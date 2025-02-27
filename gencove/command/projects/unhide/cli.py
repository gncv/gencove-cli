"""Unhide projects shell command definition."""
import click

from gencove.command.common_cli_options import add_options, common_options
from gencove.command.utils import handle_exception, validate_uuid_list
from gencove.constants import Credentials, Optionals
from gencove.logger import echo_debug

from .main import Unhide


@click.command("unhide")
@click.argument(
    "project_ids",
    required=True,
    callback=validate_uuid_list,
)
@add_options(common_options)
def unhide_projects(  # pylint: disable=too-many-arguments
    project_ids,
    host,
    email,
    password,
    api_key,
):
    """Unhide projects.

    `PROJECT_IDS`: comma-separted list of projects to be unhidden.
    """
    echo_debug(f"Project ids translation: {project_ids}")

    if not project_ids:
        handle_exception("No project ids provided")

    Unhide(
        project_ids,
        Credentials(email=email, password=password, api_key=api_key),
        Optionals(host=host),
    ).run()
