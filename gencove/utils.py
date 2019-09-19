"""Gencove CLI utils."""
import os

import boto3
from boto3.s3.transfer import TransferConfig

from botocore.credentials import RefreshableCredentials
from botocore.exceptions import ClientError
from botocore.session import get_session

import click

import progressbar

from gencove.constants import FASTQ_EXTENSIONS  # noqa: I100
from gencove.logger import echo_debug


KB = 1024
MB = KB * 1024
GB = MB * 1024
NUM_MB_IN_CHUNK = 100
CHUNK_SIZE = NUM_MB_IN_CHUNK * MB


def get_s3_client_refreshable(refresh_method):
    """Return thread-safe s3 client with refreshable credentials.

    :param refresh_method: function that can get fresh credentials
    """
    session = get_session()
    session_credentials = RefreshableCredentials.create_from_metadata(
        metadata=refresh_method(),
        refresh_using=refresh_method,
        method="sts-assume-role",
    )
    # pylint: disable=protected-access
    session._credentials = session_credentials
    boto3_session = boto3.Session(botocore_session=session)
    return boto3_session.client(
        "s3",
        endpoint_url=os.environ.get("GENCOVE_LOCALSTACK_S3_ENDPOINT") or None,
    )


def _progress_bar_update(pbar):
    """Update progress bar manually.

    Helper method for S3 Transfer,
    which needs a callback to update the progressbar.

    :param pbar: progressbar.ProgressBar instance
    :returns
        a function that in turn accepts chunk that is used to update the
        progressbar.
    """
    # noqa: D202
    def _update_pbar(chunk_uploaded_in_bytes):
        pbar.update(pbar.value + chunk_uploaded_in_bytes)

    return _update_pbar


def get_progress_bar(total_size, action):
    """Get progressbar.ProgressBar instance.

    :param total_size: int
    :param action: str that will be prepended to the progressbar.
        i.e "Uploading: " or "Downloading: "

    :returns progressbar.ProgressBar instance
    """
    return progressbar.ProgressBar(
        max_value=total_size,
        widgets=[
            action,
            progressbar.Percentage(),
            " ",
            progressbar.Bar(marker="#", left="[", right="]"),
            " ",
            progressbar.ETA(),
            " ",
            progressbar.Timer(),
            " ",
            progressbar.FileTransferSpeed(),
        ],
        redirect_stdout=True,
    )


def upload_file(s3_client, file_name, bucket, object_name=None):
    """Upload a file to an S3 bucket.

    :param s3_client: Boto s3 client
    :param file_name: File to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name. If not specified then file_name is used
    :return: True if file was uploaded, else False
    """
    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = file_name

    # Upload the file
    try:
        # Set desired multipart threshold value of 5GB
        config = TransferConfig(
            multipart_threshold=CHUNK_SIZE,
            multipart_chunksize=CHUNK_SIZE,
            use_threads=True,
            max_concurrency=10,
        )

        progress_bar = get_progress_bar(
            os.path.getsize(file_name), "Uploading: "
        )
        progress_bar.start()
        s3_client.upload_file(
            file_name,
            bucket,
            object_name,
            Config=config,
            Callback=_progress_bar_update(progress_bar),
        )
        progress_bar.finish()
    except ClientError as err:
        click.echo(
            "Failed to upload file {}: {}".format(file_name, err), err=True
        )
        return False
    return True


def seek_files_to_upload(path, path_root=""):
    """Generate a list of valid fastq files."""
    for root, dirs, files in os.walk(path):
        files.sort()
        for file in files:
            file_path = os.path.join(path_root, root, file)

            if file_path.lower().endswith(FASTQ_EXTENSIONS):
                echo_debug("Found file to upload: {}".format(file_path))
                yield file_path

        dirs.sort()
        for folder in dirs:
            seek_files_to_upload(folder, root)


def get_filename_from_path(path):
    """Cross OS get file name utility."""
    return os.path.normpath(path)


def login(api_client, email, password):
    """Login user into Gencove's system."""
    if not email or not password:
        click.echo("Login required")
        email = email or click.prompt("Email", type=str)
        password = password or click.prompt(
            "Password", type=str, hide_input=True
        )
    api_client.login(email, password)
    echo_debug("User logged in successfully")
    return api_client
