"""Gencove CLI utils."""
import os
import re

import boto3

from botocore.credentials import RefreshableCredentials
from botocore.session import get_session

import click

import progressbar

from gencove.client import APIClientError  # noqa: I100
from gencove.logger import echo, echo_debug, echo_warning

KB = 1024
MB = KB * 1024
GB = MB * 1024
NUM_MB_IN_CHUNK = 100
CHUNK_SIZE = NUM_MB_IN_CHUNK * MB
FILENAME_RE = re.compile("filename=(.+)")


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


def get_progress_bar(total_size, action):
    """Get progressbar.ProgressBar instance for file transfer.

    Args:
        total_size: int
        action: str that will be prepended to the progressbar.
            i.e "Uploading: " or "Downloading: "

    Returns:
        progressbar.ProgressBar instance
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


def get_regular_progress_bar(total_size, action):
    """Get progressbar.ProgressBar instance.

    Args:
        total_size: int
        action: str that will be prepended to the progressbar.
            i.e "Uploading: " or "Downloading: "

    Returns:
        progressbar.ProgressBar instance
    """
    return progressbar.ProgressBar(
        max_value=total_size,
        redirect_stdout=True,
        widgets=[
            action,
            progressbar.Percentage(),
            " ",
            progressbar.Bar(marker="#", left="[", right="]"),
            " ",
            progressbar.ETA(),
            " ",
            progressbar.Timer(),
        ],
    )


def validate_credentials(credentials):
    """Validate user credentials."""
    if credentials.email and credentials.password and credentials.api_key:
        echo_debug("User provided 2 sets of credentials.")
        echo_warning(
            "Multiple sets of credentials provided."
            "Please provide either username/password or API key."
        )
        return False

    return True


def login(api_client, credentials):
    """Login user into Gencove's system."""
    if credentials.api_key:
        echo_debug("User authorized via api key")
        api_client.set_api_key(credentials.api_key)
        return True

    email = credentials.email
    password = credentials.password

    if not credentials.email or not credentials.password:
        echo("Login required")
        email = email or click.prompt("Email", type=str, err=True)
        password = password or click.prompt(
            "Password", type=str, hide_input=True, err=True
        )

    try:
        api_client.login(email, password)
        echo_debug("User logged in successfully")
        return True
    except APIClientError as err:
        echo_debug("Failed to login: {}".format(err))
        echo_warning(
            "Failed to login. Please verify your credentials and try again"
        )
        return False


def batchify(items_list, batch_size=500):
    """Generate batches from items list.

    Args:
        items_list (list): list that will be batchified.
        batch_size (int, default=500): batch size that will be returned.
            last batch is not promised to be exactly the length of batch_size.

    Returns:
        subset of items_list
    """
    total = len(items_list)
    left_to_process = total
    start = 0
    while left_to_process >= 0:
        end = start + batch_size
        if end > total:
            end = total
        yield items_list[start:end]
        start += batch_size
        left_to_process -= batch_size
