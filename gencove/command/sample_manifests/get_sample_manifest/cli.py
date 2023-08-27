"""Get sample manifest shell command definition."""
import click

from gencove.command.common_cli_options import add_options, common_options
from gencove.command.utils import validate_uuid
from gencove.constants import Credentials, Optionals

from .main import GetSampleManifest


@click.command("get-sample-manifest")
@click.argument("manifest_id", callback=validate_uuid)
@click.argument("destination")
@add_options(common_options)
def get_sample_manifest(  # pylint: disable=too-many-arguments
    manifest_id,
    destination,
    host,
    email,
    password,
    api_key,
):
    """Download a sample manifest to a specified destination directory."""
    GetSampleManifest(
        manifest_id,
        destination,
        Credentials(email=email, password=password, api_key=api_key),
        Optionals(host=host),
    ).run()
