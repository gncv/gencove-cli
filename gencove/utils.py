"""Gencove CLI utils."""
import os
import re
from urllib.parse import parse_qs, urlparse

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


def login(api_client, email, password):
    """Login user into Gencove's system."""
    if not email or not password:
        echo("Login required")
        email = email or click.prompt("Email", type=str)
        password = password or click.prompt(
            "Password", type=str, hide_input=True
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


def get_filename_from_download_url(content_disposition, url):
    """Deduce filename from content disposition or url.

    Args:
        content_disposition (str): Request header Content-Disposition
        url (str): URL string
    """
    filename_match = re.findall(FILENAME_RE, content_disposition)
    if not filename_match:
        echo_debug(
            "Content disposition had no filename. Trying url query params"
        )
        filename = re.findall(FILENAME_RE, parse_qs(urlparse(url).query))
    else:
        filename = filename_match[0]
    if not filename:
        echo_debug(
            "URL didn't contain filename query argument. "
            "Assume filename from url"
        )
        filename = urlparse(url).path.split("/")[-1]
    echo_debug("Deduced filename to be: {}".format(filename))
    return filename


def deliverable_type_from_filename(filename):
    """Deduce deliverable type based on dot notation."""
    return ".".join(filename.split(".")[1:])
