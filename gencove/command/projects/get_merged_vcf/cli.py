"""Project get merged VCF shell command definition."""
import click

from gencove.command.common_cli_options import add_options, common_options
from gencove.constants import Credentials, Optionals

from .main import GetMergedVCF


@click.command("get-merged-vcf")
@click.argument("project_id")
@click.option(
    "--output-filename",
    help="Output filename for merged VCF file.",
    type=click.Path(),
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
def get_merged_vcf(
    project_id,
    output_filename,
    host,
    email,
    password,
    api_key,
    no_progress,
):
    """Download merged VCF file in a project."""
    GetMergedVCF(
        project_id,
        output_filename,
        Credentials(email=email, password=password, api_key=api_key),
        Optionals(host=host),
        no_progress,
    ).run()
