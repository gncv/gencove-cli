"""Sample download file shell command definition."""
import click

from gencove.command.common_cli_options import add_options, common_options
from gencove.constants import Credentials, Optionals

from .main import DownloadFile


@click.command("download-file")
@click.argument("sample_id")
@click.argument("file_type")
@click.argument("destination", type=click.File("wb"))
@add_options(common_options)
@click.option(
    "--no-progress",
    is_flag=True,
    help="If specified, no progress bar is shown.",
)
# pylint: disable=too-many-arguments
def download_file(
    sample_id,
    file_type,
    destination,
    host,
    email,
    password,
    api_key,
    no_progress,
):
    """Download sample file metadata."""
    DownloadFile(
        sample_id,
        file_type,
        destination,
        Credentials(email, password, api_key),
        Optionals(host),
        no_progress,
    ).run()
