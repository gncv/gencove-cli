"""Sample download file shell command definition."""
import sys

import click

from gencove.command.common_cli_options import add_options, common_options
from gencove.constants import Credentials, Optionals
from gencove.logger import echo_error

from .main import DownloadFile


@click.command("download-file")
@click.argument("sample_id")
@click.argument("file_type")
@click.argument("destination")
@add_options(common_options)
@click.option(
    "--no-progress",
    is_flag=True,
    help="If specified, no progress bar is shown.",
)
@click.option(
    "--checksum",
    is_flag=True,
    help="If specified, an additional checksum file will be downloaded.",
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
    checksum,
):  # noqa: D413,D301,D412 # pylint: disable=C0301
    """Download sample file metadata.

    SAMPLE_ID   specific sample for which to download the results

    FILE_TYPE   specific deliverable to download results for

    DESTINATION path/to/file

    Examples:

        Download sample:

            gencove samples download-file e6b45af7-07c5-4a6d-9f97-6e1efbf3e215 ancestry-json ancestry.json

        Download and print to stdout then compress using gzip:

            gencove samples download-file e6b45af7-07c5-4a6d-9f97-6e1efbf3e215 ancestry-json - | gzip > ancestry.json.gz
    \f
    .. ignore::
        Args:
            sample_id (str): specific sample for which
                to download the results.
            file_type (str): specific deliverable to download
                results for.
            destination (str): path/to/file.
            no_progress (bool, optional, default False): do not show progress
                bar.
            checksum (bool, optional, default False): download additional checksum
                files for each deliverable.

    """  # noqa: E501
    if destination in ("-", "/dev/stdout"):
        DownloadFile(
            sample_id,
            file_type,
            sys.stdout.buffer,
            Credentials(email=email, password=password, api_key=api_key),
            Optionals(host=host),
            no_progress,
            checksum,
        ).run()
    else:
        try:
            with open(destination, "wb") as destination_file:
                DownloadFile(
                    sample_id,
                    file_type,
                    destination_file,
                    Credentials(email=email, password=password, api_key=api_key),
                    Optionals(host=host),
                    no_progress,
                    checksum,
                ).run()
        except IsADirectoryError:
            echo_error(
                "Please specify a file path (not directory path) for DESTINATION"
            )
            raise click.Abort()  # pylint: disable=raise-missing-from
