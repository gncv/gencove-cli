"""Project create merged VCF shell command definition."""
import click

from gencove.command.common_cli_options import add_options, common_options
from gencove.command.utils import validate_uuid
from gencove.constants import Credentials, Optionals

from .main import CreateMergedVCF


@click.command("create-merged-vcf")
@click.argument("project_id", callback=validate_uuid)
@add_options(common_options)
def create_merged_vcf(
    project_id,
    host,
    email,
    password,
    api_key,
):
    """Merge VCF files in a project.

    `PROJECT_ID`: Gencove project ID
    """
    CreateMergedVCF(
        project_id,
        Credentials(email=email, password=password, api_key=api_key),
        Optionals(host=host),
    ).run()
