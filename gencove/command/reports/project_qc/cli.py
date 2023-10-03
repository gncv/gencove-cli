"""Get project QC report shell command definition."""

import click

from gencove.command.common_cli_options import add_options, common_options
from gencove.command.utils import validate_uuid
from gencove.constants import Credentials, Optionals

from .main import ProjectQCReport


@click.command("project-qc")
@click.argument("project_id", callback=validate_uuid)
@click.option(
    "--columns",
    default=None,
    help="A comma separated list of columns to include in the report. "
    "By default, all columns are included.",
)
@click.option(
    "--output-filename",
    help="Output filename for the output report. "
    "If not supplied, will download the file to the current directory.",
    type=click.Path(),
    default=None,
    required=False,
)
@add_options(common_options)
def project_qc(  # pylint: disable=too-many-arguments
    project_id,
    columns,
    output_filename,
    host,
    email,
    password,
    api_key,
):
    """Download a project QC CSV report to a specified filename.

    `PROJECT_ID`: Gencove project ID
    """
    ProjectQCReport(
        project_id,
        columns,
        output_filename,
        Credentials(email=email, password=password, api_key=api_key),
        Optionals(host=host),
    ).run()
