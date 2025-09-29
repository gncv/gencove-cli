"""Project get jointcalled VCF shell command definition."""
import click

from gencove.command.common_cli_options import add_options, common_options
from gencove.command.utils import validate_uuid
from gencove.constants import Credentials, Optionals

from .main import GetJointcalledVCF


@click.command("get-jointcalled-vcf")
@click.argument("project_id", callback=validate_uuid)
@click.option(
    "--output-folder",
    help="Output folder for jointcalled VCF files.",
    type=click.Path(file_okay=False, writable=True, dir_okay=True),
    required=False,
    default=None,
)
@add_options(common_options)
@click.option(
    "--no-progress",
    is_flag=True,
    help="If specified, no progress bar is shown.",
)
# pylint: disable=too-many-arguments
def get_jointcalled_vcf(
    project_id,
    output_folder,
    host,
    email,
    password,
    api_key,
    no_progress,
):
    """Download jointcalled VCF files in a project.

    `PROJECT_ID`: Gencove project ID
    """
    GetJointcalledVCF(
        project_id,
        output_folder,
        Credentials(email=email, password=password, api_key=api_key),
        Optionals(host=host),
        no_progress,
    ).run()
