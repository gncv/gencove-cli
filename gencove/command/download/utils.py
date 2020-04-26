"""Download command utilities."""
import json
import os
import re

try:
    # python 3.7
    from urllib.parse import urlparse, parse_qs  # noqa
except ImportError:
    # python 2.7
    from urlparse import urlparse, parse_qs  # noqa

import backoff

import requests

from gencove.constants import (  # noqa: I100
    DownloadTemplateParts,
    MAX_RETRY_TIME_SECONDS,
)
from gencove.logger import echo, echo_debug
from gencove.utils import get_progress_bar

from .constants import (
    CHUNK_SIZE,
    DEFAULT_FILENAME_TOKEN,
    FILENAME_RE,
    FILE_TYPES_MAPPER,
    FilePrefix,
)


def _get_prefix_parts(full_prefix):
    """Extract directories prefix parts from."""
    prefix_parts = full_prefix.split("/")
    file_name, _, file_ext = prefix_parts[-1].partition(".")
    return FilePrefix(
        "/".join(prefix_parts[:-1]),
        file_name,
        file_ext,
        DEFAULT_FILENAME_TOKEN in full_prefix,
    )


def get_filename_from_download_url(url):
    """Deduce filename from url.

    Args:
        url (str): URL string

    Returns:
        str: filename
    """
    try:
        filename = re.findall(
            FILENAME_RE,
            parse_qs(urlparse(url).query)["response-content-disposition"][0],
        )[0]
    except (KeyError, IndexError):
        echo_debug(
            "URL didn't contain filename query argument. "
            "Assume filename from url"
        )
        filename = urlparse(url).path.split("/")[-1]

    return filename


def deliverable_type_from_filename(filename):
    """Deduce deliverable type based on dot notation."""
    filetype = ".".join(filename.split(".")[1:])
    echo_debug(
        "Deduced filetype to be: {} "
        "from filename: {}".format(filetype, filename)
    )
    return filetype


def _create_filepath(download_to, prefix_dirs, filename):
    """Build full file path and ensure that directory structure exists.

    Args:
        download_to (str): top level directory path
        prefix_dirs (str): subdirectories structure to create under
            download_to.
        filename (str): name of the file inside download_to/file_prefix
            structure.
    """
    echo_debug("_create_filepath Downloading to: {}".format(download_to))
    echo_debug("_create_filepath file prefix is: {}".format(prefix_dirs))

    path = os.path.join(download_to, prefix_dirs)
    # Cross-platform cross-python-version directory creation
    if not os.path.exists(path):
        echo_debug("creating path: {}".format(path))
        os.makedirs(path)

    file_path = os.path.join(path, filename)
    echo_debug("Deduced full file path is {}".format(file_path))
    return file_path


def build_file_path(
    deliverable, file_with_prefix, download_to, filename=None
):
    """Create and return file system path where the file will be downloaded to.

    Args:
        deliverable (dict): used to get download url and file type
        file_with_prefix (str): used as a template for download path
        download_to (str): general location where to download the file to

    Returns:
         str : file path on current file system
    """
    prefix = _get_prefix_parts(file_with_prefix)
    # fmt: off
    source_filename = filename if filename else get_filename_from_download_url(deliverable["download_url"])  # noqa: E501  # pylint: disable=line-too-long
    # fmt: on

    if prefix.use_default_filename:
        destination_filename = prefix.filename
    elif prefix.file_extension:
        destination_filename = "{}.{}".format(
            prefix.filename, prefix.file_extension
        )
    else:
        destination_filename = "{}.{{{}}}".format(
            prefix.filename, DownloadTemplateParts.file_extension
        )

    # turning off formatting for improved code readability
    # fmt: off
    destination_filename = destination_filename.format(
        **{
            DownloadTemplateParts.file_type: FILE_TYPES_MAPPER.get(deliverable["file_type"]) or deliverable["file_type"],  # noqa: E501  # pylint: disable=line-too-long
            DownloadTemplateParts.file_extension: deliverable_type_from_filename(source_filename),  # noqa: E501  # pylint: disable=line-too-long
            DownloadTemplateParts.default_filename: source_filename,
        }
    )
    # fmt: on

    echo_debug(
        "Calculated destination filename: {}".format(destination_filename)
    )
    return _create_filepath(download_to, prefix.dirs, destination_filename)


def fatal_request_error(err=None):
    """Give up retrying if the error code is in fatal range.

    Returns:
        bool: True if to giveup on backing off, False it to continue.
    """
    if not err or not err.response:
        return False
    if err.response.status_code == 403:
        # download url needs to be refreshed, give up on backoff
        return True
    # retry 4xx or 5xx and all else not
    return not 400 <= err.response.status_code <= 600


@backoff.on_exception(
    backoff.expo,
    (
        requests.exceptions.HTTPError,
        requests.exceptions.ConnectionError,
        requests.exceptions.Timeout,
    ),
    max_time=MAX_RETRY_TIME_SECONDS,
    giveup=fatal_request_error,
)
def download_file(file_path, download_url, skip_existing=True):
    """Download a file to file system.

    Args:
        file_path (str): full file path, according to destination
            and download template
        download_url (str): url of the file to download
        skip_existing (bool): skip already downloaded files

    Returns:
        str : file path
            location of the downloaded file
    """

    file_path_tmp = "{}.tmp".format(file_path)
    if os.path.exists(file_path_tmp):
        file_mode = "ab"
        headers = dict(
            Range="bytes={}-".format(os.path.getsize(file_path_tmp))
        )
        echo("Resuming previous download: {}".format(file_path))
    else:
        file_mode = "wb"
        headers = dict()
        echo("Downloading file to {}".format(file_path))

    stream_params = dict(
        stream=True, allow_redirects=False, headers=headers, timeout=30
    )

    with requests.get(download_url, **stream_params) as req:
        req.raise_for_status()
        total = int(req.headers["content-length"])
        # pylint: disable=C0330
        if (
            skip_existing
            and os.path.isfile(file_path)
            and os.path.getsize(file_path) == total
        ):
            echo("Skipping existing file: {}".format(file_path))
            return file_path

        echo_debug("Starting to download file to: {}".format(file_path))

        with open(file_path_tmp, file_mode) as downloaded_file:
            pbar = get_progress_bar(
                int(req.headers["content-length"]), "Downloading: "
            )
            pbar.start()
            for chunk in req.iter_content(chunk_size=CHUNK_SIZE):
                downloaded_file.write(chunk)
                pbar.update(pbar.value + len(chunk))
            pbar.finish()

        # Cross-platform cross-python-version file overwriting
        if os.path.exists(file_path):
            echo_debug(
                "Found old file under same name: {}. "
                "Removing it.".format(file_path)
            )
            os.remove(file_path)
        os.rename(file_path_tmp, file_path)
        echo("Finished downloading a file: {}".format(file_path))
        return file_path


def save_qc_file(path, content):
    """Helper function to save qc metrics to json file.

    Args:
        path(str): full file path where qc metrics will be saved
        content(list of dict): list of qc metrics to be saved

    Returns:
        None
    """
    echo("Downloading file to: {}".format(path))
    with open(path, "w") as qc_file:
        json.dump(content, qc_file)


def fatal_process_sample_error(err):
    """Give up retrying if the error code is different from 403.

    If the error code is 403, we need to refresh the download url and try
    processing the sample again.

    Returns:
        bool: True if to giveup on backing off, False it to continue.
    """
    return err.response.status_code != 403


def get_download_template_format_params(client_id, gencove_id):
    """Return format parts for download template.

    Args:
        client_id (str): sample client id
        gencove_id (str): sample gencove id

    Returns:
        format parts : dict
    """
    return {
        DownloadTemplateParts.client_id: client_id,
        DownloadTemplateParts.gencove_id: gencove_id,
        DownloadTemplateParts.file_type: "{{{}}}".format(
            DownloadTemplateParts.file_type
        ),
        DownloadTemplateParts.file_extension: "{{{}}}".format(
            DownloadTemplateParts.file_extension
        ),
        DownloadTemplateParts.default_filename: "{{{}}}".format(
            DownloadTemplateParts.default_filename
        ),
    }
