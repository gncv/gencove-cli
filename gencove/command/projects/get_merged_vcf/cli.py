"""Project get merged VCF shell command definition."""
import click

from gencove.command.common_cli_options import add_options, common_options
from gencove.constants import Credentials, Optionals

from .main import GetMergedVCF


@click.command("get-merged-vcf")
@click.argument("project_id")
@click.option(
    "--download-urls",
    help="Output a list of urls in a JSON format.",
    is_flag=True,
)
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
    download_urls,
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
        download_urls,
        output_filename,
        Credentials(email=email, password=password, api_key=api_key),
        Optionals(host=host),
        no_progress,
    ).run()
