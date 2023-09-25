"""Get project QC report shell command definition."""
import click

from gencove.command.common_cli_options import add_options, common_options
from gencove.command.utils import validate_destination_exists, validate_uuid
from gencove.constants import Credentials, Optionals

from .main import ProjectQCReport


@click.command("project-qc")
@click.argument("project_id", callback=validate_uuid)
@click.argument("destination", callback=validate_destination_exists)
@add_options(common_options)
def project_qc(  # pylint: disable=too-many-arguments
    project_id,
    destination,
    host,
    email,
    password,
    api_key,
):
    """Download a project QC report to a specified destination directory.

    `PROJECT_ID`: Gencove project ID

    `DESTINATION`: path/to/save/manfiest/to
    """
    ProjectQCReport(
        project_id,
        destination,
        Credentials(email=email, password=password, api_key=api_key),
        Optionals(host=host),
    ).run()
