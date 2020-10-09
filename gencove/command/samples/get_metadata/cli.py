"""Sample get metadata shell command definition."""
import click

from gencove.command.common_cli_options import add_options, common_options
from gencove.constants import Credentials, Optionals

from .main import GetMetadata


@click.command("get-metadata")
@click.argument("sample_id")
@click.option(
    "--output-filename",
    help="Output filename for the metadata.",
    type=click.Path(),
    default="-",
    required=False,
)
@add_options(common_options)
# pylint: disable=too-many-arguments
def get_metadata(
    sample_id,
    output_filename,
    host,
    email,
    password,
    api_key,
):
    """Get sample metadata."""
    GetMetadata(
        sample_id,
        output_filename,
        Credentials(email, password, api_key),
        Optionals(host),
    ).run()
