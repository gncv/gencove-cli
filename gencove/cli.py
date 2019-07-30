"""Gencove CLI application."""
import os
import uuid
from datetime import datetime

import click

from gencove import client, version
from gencove.constants import (
    FASTQ_EXTENSIONS,
    HOST,
    TMP_UPLOADS_WARNING,
    UPLOAD_PREFIX,
    UPLOAD_STATUSES,
)
from gencove.logger import echo, echo_debug, echo_warning
from gencove.utils import (
    get_filename_from_path,
    get_s3_client_refreshable,
    seek_files_to_upload,
    upload_file,
)


@click.group()
@click.version_option(version=version.version())
def cli():
    """Gencove command line interface."""


@cli.command()
@click.argument("source")
@click.argument("destination", required=False)
@click.option(
    "--host",
    default=HOST,
    help="Optional Gencove API host, including http/s protocol. "
    "Defaults to https://api.gencove.com",
)
@click.option(
    "--email",
    default=lambda: os.environ.get("GENCOVE_EMAIL", ""),
    help="Gencove user email to be used in login. "
    "Can be passed as GENCOVE_EMAIL environment variable",
)
@click.option(
    "--password",
    default=lambda: os.environ.get("GENCOVE_PASSWORD", ""),
    help="Gencove user password to be used in login. "
    "Can be passed as GENCOVE_PASSWORD environment variable",
)
def sync(source, destination, host, email, password):
    """Upload FASTQ files to Gencove system.

    Arguments:

    source - folder that contains fastq files to be uploaded
    in one of the following formats:

        .fastq.gz, .fastq.bgz, .fq.gz, .fq.bgz

    destination - (optional) 'gncs://' notated folder on Gencove system,
    where the files will be uploaded.
    """
    echo_debug("Host is {}".format(host))

    files_to_upload = list(seek_files_to_upload(source))
    if not files_to_upload:
        echo(
            "No FASTQ files found in the path. "
            "Only following files are accepted: {}".format(FASTQ_EXTENSIONS),
            err=True,
        )
        return

    if destination and not destination.startswith(UPLOAD_PREFIX):
        echo(
            "Invalid destination path. Must start with '{}'".format(
                UPLOAD_PREFIX
            ),
            err=True,
        )
        return

    echo_warning(TMP_UPLOADS_WARNING, err=True)

    if not destination:
        destination = "{}cli-{}-{}".format(
            UPLOAD_PREFIX,
            datetime.utcnow().strftime("%Y%m%d%H%M%S"),
            uuid.uuid4().hex,
        )
        echo("Files will be uploaded to: {}".format(destination))

    if not email or not password:
        click.echo("Login required")
        email = email or click.prompt("Email", type=str)
        password = password or click.prompt(
            "Password", type=str, hide_input=True
        )

    api_client = client.APIClient(host)
    api_client.login(email, password)
    s3_client = get_s3_client_refreshable(api_client.get_upload_credentials)

    for file_path in files_to_upload:
        filename = get_filename_from_path(file_path)
        gncv_notated_path = "{}/{}".format(destination, filename)
        echo("Uploading {} to {}".format(file_path, gncv_notated_path))

        upload_details = api_client.get_upload_details(gncv_notated_path)
        if upload_details["last_status"]["status"] == UPLOAD_STATUSES.done:
            echo(
                "File was already uploaded: {}".format(get_filename_from_path)
            )
            continue

        upload_file(
            s3_client=s3_client,
            file_name=file_path,
            bucket=upload_details["s3"]["bucket"],
            object_name=upload_details["s3"]["object_name"],
        )

    echo("All files were successfully synced.")


if __name__ == "__main__":
    cli()
