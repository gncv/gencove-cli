"""Download command utilities."""
import json
import os
import re
from urllib.parse import parse_qs, urlparse

import backoff

import requests

from gencove import client  # noqa: I100
from gencove.constants import (  # noqa: I100
    DownloadTemplateParts,
    MAX_RETRY_TIME_SECONDS,
)
from gencove.logger import echo_debug, echo_info, echo_warning
from gencove.models import SampleFile
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
        dirs="/".join(prefix_parts[:-1]),
        filename=file_name,
        file_extension=file_ext,
        use_default_filename=(DEFAULT_FILENAME_TOKEN in full_prefix),
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
            "URL didn't contain filename query argument. Assume filename from url"
        )
        filename = urlparse(url).path.split("/")[-1]

    return filename


def deliverable_type_from_filename(filename):
    """Deduce deliverable type based on dot notation."""
    filetype = ".".join(filename.split(".")[1:])
    echo_debug(f"Deduced filetype to be: {filetype} from filename: {filename}")
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
    echo_debug(f"_create_filepath Downloading to: {download_to}")
    echo_debug(f"_create_filepath file prefix is: {prefix_dirs}")

    path = os.path.join(download_to, prefix_dirs)
    # Cross-platform cross-python-version directory creation
    if not os.path.exists(path):
        echo_debug(f"creating path: {path}")
        os.makedirs(path)

    file_path = os.path.join(path, filename)
    echo_debug(f"Deduced full file path is {file_path}")
    return file_path


def build_file_path(deliverable, file_with_prefix, download_to, filename=None):
    """Create and return file system path where the file will be downloaded to.

    Args:
        deliverable (dict): used to get download url and file type
        file_with_prefix (str): used as a template for download path
        download_to (str): general location where to download the file to

    Returns:
         str : file path on current file system
    """
    prefix = _get_prefix_parts(file_with_prefix)
    download_url, file_type = "", ""
    if isinstance(deliverable, SampleFile):
        download_url, file_type = (
            deliverable.download_url,
            deliverable.file_type,
        )
    else:
        download_url, file_type = (
            deliverable.get("download_url"),
            deliverable.get("file_type"),
        )
    source_filename = (
        filename if filename else get_filename_from_download_url(download_url)
    )

    destination_filename = prefix.filename
    if prefix.file_extension:
        destination_filename = f"{prefix.filename}.{prefix.file_extension}"

    # turning off formatting for improved code readability
    # fmt: off
    destination_filename = destination_filename.format(
        **{
            DownloadTemplateParts.FILE_TYPE.value: FILE_TYPES_MAPPER.get(file_type) or file_type,  # noqa: E501  # pylint: disable=line-too-long
            DownloadTemplateParts.FILE_EXTENSION.value: deliverable_type_from_filename(source_filename),  # noqa: E501  # pylint: disable=line-too-long
            DownloadTemplateParts.DEFAULT_FILENAME.value: source_filename,
        }
    )
    # fmt: on

    echo_debug(f"Calculated destination filename: {destination_filename}")
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
def download_file(file_path, download_url, skip_existing=True, no_progress=False):
    """Download a file to file system.

    Args:
        file_path (str): full file path, according to destination
            and download template
        download_url (str): url of the file to download
        skip_existing (bool): skip already downloaded files
        no_progress (bool): don't show progress bar

    Returns:
        str : file path
            location of the downloaded file
    """

    file_path_tmp = f"{file_path}.tmp"
    if os.path.exists(file_path_tmp):
        file_mode = "ab"
        headers = dict(Range=f"bytes={os.path.getsize(file_path_tmp)}-")
        echo_info(f"Resuming previous download: {file_path}")
    else:
        file_mode = "wb"
        headers = {}
        echo_info(f"Downloading file to {file_path}")

    stream_params = dict(
        stream=True, allow_redirects=False, headers=headers, timeout=30
    )

    with requests.get(download_url, **stream_params) as req:
        req.raise_for_status()
        total = int(req.headers["content-length"])
        # pylint: disable=E0012,C0330
        if (
            skip_existing
            and os.path.isfile(file_path)
            and os.path.getsize(file_path) == total
        ):
            echo_info(f"Skipping existing file: {file_path}")
            return file_path

        echo_debug(f"Starting to download file to: {file_path}")

        with open(file_path_tmp, file_mode) as downloaded_file:
            if not no_progress:
                pbar = get_progress_bar(
                    int(req.headers["content-length"]), "Downloading: "
                )
                pbar.start()
            for chunk in req.iter_content(chunk_size=CHUNK_SIZE):
                downloaded_file.write(chunk)
                if not no_progress:
                    pbar.update(pbar.value + len(chunk))
            if not no_progress:
                pbar.finish()

        # Cross-platform cross-python-version file overwriting
        if os.path.exists(file_path):
            echo_debug(f"Found old file under same name: {file_path}. Removing it.")
            os.remove(file_path)
        os.rename(file_path_tmp, file_path)
        echo_info(f"Finished downloading a file: {file_path}")
        return file_path


def save_metadata_file(path, api_client, sample_id, skip_existing=True):
    """Helper function to save metadata to json file.

    Args:
        path(str): full file path where metadata will be saved
        api_client(APIClient): an instance of the client to make a call
        sample_id(str of uuid): sample gencove id
        skip_existing(bool): option of skipping the existing file

    Returns:
        None
    """
    if skip_existing and os.path.isfile(path) and os.path.getsize(path):
        echo_info(f"Skipping existing file: {path}")
        return
    try:
        metadata = api_client.get_metadata(sample_id)
    except client.APIClientError:
        echo_warning("Error getting sample metadata.")
        raise
    echo_info(f"Downloading file to: {path}")
    with open(path, "w", encoding="utf-8") as metadata_file:
        metadata_file.write(metadata.json())
    echo_info(f"Finished downloading a file: {path}")


def save_qc_file(path, api_client, sample_id, skip_existing=True):
    """Helper function to save qc metrics to json file.

    Args:
        path(str): full file path where qc metrics will be saved
        api_client(APIClient): an instance of the client to make a call
        sample_id(str of uuid): sample gencove id
        skip_existing(bool): option of skipping the existing file

    Returns:
        None
    """
    if skip_existing and os.path.isfile(path) and os.path.getsize(path):
        echo_info(f"Skipping existing file: {path}")
        return
    try:
        sample_qcs = api_client.get_sample_qc_metrics(sample_id).results
    except client.APIClientError:
        echo_warning("Error getting sample quality control metrics.")
        raise
    echo_info(f"Downloading file to: {path}")
    with open(path, "w", encoding="utf-8") as qc_file:
        content = json.dumps(sample_qcs, cls=client.CustomEncoder)
        qc_file.write(content)
    echo_info(f"Finished downloading a file: {path}")


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
        DownloadTemplateParts.CLIENT_ID.value: client_id,
        DownloadTemplateParts.GENCOVE_ID.value: gencove_id,
        DownloadTemplateParts.FILE_TYPE.value: f"{{{DownloadTemplateParts.FILE_TYPE.value}}}",  # noqa: E501  # pylint: disable=line-too-long
        DownloadTemplateParts.FILE_EXTENSION.value: f"{{{DownloadTemplateParts.FILE_EXTENSION.value}}}",  # noqa: E501  # pylint: disable=line-too-long
        DownloadTemplateParts.DEFAULT_FILENAME.value: f"{{{DownloadTemplateParts.DEFAULT_FILENAME.value}}}",  # noqa: E501  # pylint: disable=line-too-long
    }
