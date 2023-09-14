"""Project create sample manifest shell command definition."""
import click

from gencove.command.common_cli_options import add_options, common_options
from gencove.command.utils import validate_uuid
from gencove.constants import Credentials, Optionals

from .main import CreateSampleManifest


@click.command("create-sample-manifest")
@click.argument("project_id", callback=validate_uuid)
@click.argument("sample_manifest")
@add_options(common_options)
def create_sample_manifest(  # pylint: disable=too-many-arguments
    project_id,
    sample_manifest,
    host,
    email,
    password,
    api_key,
):
    """Create a sample manifest in a project by uploading a CSV file.

    `PROJECT_ID`: Gencove project ID

    `SAMPLE_MANIFEST`: .csv file files that contains a table of information
        about a sequencing run
    """
    CreateSampleManifest(
        project_id,
        sample_manifest,
        Credentials(email=email, password=password, api_key=api_key),
        Optionals(host=host),
    ).run()
