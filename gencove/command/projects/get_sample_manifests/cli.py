"""Project get sample manifests shell command definition."""
import click

from gencove.command.common_cli_options import add_options, common_options
from gencove.command.utils import validate_uuid, validate_destination_exists
from gencove.constants import Credentials, Optionals

from .main import GetSampleManifests


@click.command("get-sample-manifests")
@click.argument("project_id", callback=validate_uuid)
@click.argument("destination", callback=validate_destination_exists)
@add_options(common_options)
def get_sample_manifests(  # pylint: disable=too-many-arguments
    project_id,
    destination,
    host,
    email,
    password,
    api_key,
):
    """Download all sample manifests in a project to a destination directory."""
    GetSampleManifests(
        project_id,
        destination,
        Credentials(email=email, password=password, api_key=api_key),
        Optionals(host=host),
    ).run()
