"""Sample set metadata shell command definition."""
import click

from gencove.command.common_cli_options import add_options, common_options
from gencove.constants import Credentials, Optionals

from .main import SetMetadata


@click.command("set-metadata")
@click.argument("sample_id")
@click.option(
    "--json",
    help="JSON string of the metadata to be assigned to a sample.",
    required=True,
)
@add_options(common_options)
# pylint: disable=too-many-arguments
def set_metadata(
    sample_id,
    json,
    host,
    email,
    password,
    api_key,
):
    """Set sample metadata.

    `SAMPLE_ID`: sample for which to set the metadata
    """
    SetMetadata(
        sample_id,
        json,
        Credentials(email=email, password=password, api_key=api_key),
        Optionals(host=host),
    ).run()
