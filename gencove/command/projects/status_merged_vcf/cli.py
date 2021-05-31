"""Project status merged VCF shell command definition."""
import click

from gencove.command.common_cli_options import add_options, common_options
from gencove.constants import Credentials, Optionals

from .main import StatusMergedVCF


@click.command("status-merged-vcf")
@click.argument("project_id")
@add_options(common_options)
def status_merged_vcf(
    project_id,
    host,
    email,
    password,
    api_key,
):
    """Get status of merge VCF files job in a project."""
    StatusMergedVCF(
        project_id,
        Credentials(email=email, password=password, api_key=api_key),
        Optionals(host=host),
    ).run()
