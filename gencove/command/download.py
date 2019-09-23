"""CLI command to download project results."""
import os
import re
import uuid
from collections import namedtuple

try:
    # python 3.7
    from urllib.parse import urlparse, parse_qs  # noqa
except ImportError:
    # python 2.7
    from urlparse import urlparse, parse_qs  # noqa

import requests

from gencove import client  # noqa: I100
from gencove.constants import Optionals, SAMPLE_STATUSES
from gencove.logger import echo, echo_debug, echo_warning
from gencove.utils import get_progress_bar, login


ALLOWED_STATUSES_RE = re.compile(
    "{}|{}".format(SAMPLE_STATUSES.succeeded, SAMPLE_STATUSES.failed),
    re.IGNORECASE,
)
FILENAME_RE = re.compile("filename=(.+)")
KILOBYTE = 1024
MEGABYTE = 1024 * KILOBYTE
NUM_MB_IN_CHUNK = 3
CHUNK_SIZE = NUM_MB_IN_CHUNK * MEGABYTE

DownloadFilters = namedtuple(
    "Filters", ["project_id", "sample_ids", "file_types"]
)
DownloadOptions = namedtuple(  # pylint: disable=invalid-name
    "DownloadOptions", Optionals._fields + ("skip_existing",)
)


def download_deliverables(destination, filters, credentials, options):
    """Download project deliverables to a specified path on user machine.

    Args:
        destination (str): path/to/save/deliverables/to.
        filters (DownloadFilters): allows to filter project deliverables
            to be downloaded.
        credentials (constants.Credentials): login email/password.
        options (DownloadOptions): different options to tweak execution.
    """
    if not filters.project_id and not filters.sample_ids:
        echo_warning(
            "Must specify one of: project id or sample ids", err=True
        )
        return

    if filters.project_id and filters.sample_ids:
        echo_warning(
            "Must specify only one of: project id or sample ids", err=True
        )
        return

    echo_debug(
        "Host is {} downloading to {}".format(options.host, destination)
    )
    api_client = client.APIClient(options.host)
    login(api_client, credentials.email, credentials.password)

    if filters.project_id:
        echo_debug(
            "Retrieving sample ids for a project: {}".format(
                filters.project_id
            )
        )
        count = 0
        try:
            samples_generator = _get_paginated_samples(
                filters.project_id, api_client
            )
            for sample in samples_generator:
                _process_sample(
                    destination,
                    sample["id"],
                    filters.file_types,
                    api_client,
                    options.skip_existing,
                )
                count += 1

            if not count:
                echo_warning("Project has no samples to download")
                return

            echo_debug("Processed {} samples".format(count))
            return
        except client.APIClientError:
            echo_warning(
                "Project id {} not found.".format(filters.project_id)
            )
            return

    for sample_id in filters.sample_ids:
        _process_sample(
            destination,
            sample_id,
            filters.file_types,
            api_client,
            options.skip_existing,
        )


def _get_paginated_samples(project_id, api_client):
    """Generate for project samples that traverses all pages."""
    get_samples = True
    next_page = None
    while get_samples:
        echo_debug("Getting page: {}".format(next_page or 1))
        req = api_client.get_project_samples(project_id, next_page)
        for sample in req["results"]:
            yield sample
        next_page = req["meta"]["next"]
        get_samples = next_page is not None


def _download_file(download_to, file_prefix, url, skip_existing):
    """Download a file to file system.

    Args:
        download_to (str): system/path/to/save/file/to
        file_prefix (str): <client id>/<gencove sample id> to nest downloaded
            file.
        url (str): signed url from S3 to download the file from.
        skip_existing (bool): skip downloading existing files.
    """
    with requests.get(url, stream=True) as req:
        req.raise_for_status()
        filename = _get_filename(req.headers["content-disposition"], url)
        filename_tmp = "download-{}.tmp".format(uuid.uuid4().hex)
        file_path = _create_filepath(download_to, file_prefix, filename)
        file_path_tmp = _create_filepath(
            download_to, file_prefix, filename_tmp
        )
        total = int(req.headers["content-length"])

        # pylint: disable=C0330
        if (
            skip_existing
            and os.path.isfile(file_path)
            and os.path.getsize(file_path) == total
        ):
            echo("Skipping existing file: {}".format(file_path))
            return

        echo_debug("Starting to download file to: {}".format(file_path))

        with open(file_path_tmp, "wb") as downloaded_file:
            pbar = get_progress_bar(total, "Downloading: ")
            pbar.start()
            for chunk in req.iter_content(chunk_size=CHUNK_SIZE):
                downloaded_file.write(chunk)
                pbar.update(pbar.value + len(chunk))
            pbar.finish()

        # Cross-platform cross-python-version file overwriting
        if os.path.exists(file_path):
            os.remove(file_path)
        os.rename(file_path_tmp, file_path)
        echo("Finished downloading a file: {}".format(file_path))


def _create_filepath(download_to, file_prefix, filename):
    """Build full file path and ensure that directory structure exists.

    Args:
        download_to (str): top level directory path
        file_prefix (str): subdirectories structure to create under download_to.
        filename (str): name of the file inside download_to/file_prefix
            structure.
    """
    path = os.path.join(download_to, file_prefix)
    # Cross-platform cross-python-version directory creation
    if not os.path.exists(path):
        os.makedirs(path)
    file_path = os.path.join(path, filename)
    echo_debug("Deduced full file path is {}".format(file_path))
    return file_path


def _get_filename(content_disposition, url):
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


# pylint: disable=C0330
def _process_sample(
    destination, sample_id, file_types, api_client, skip_existing
):
    """Download sample deliverables."""
    try:
        sample = api_client.get_sample_details(sample_id)
    except client.APIClientError:
        echo_warning(
            "Sample with id {} not found. "
            "Are you using client id instead of sample id?".format(sample_id)
        )
        return

    echo_debug(
        "Processing sample id {}, status {}".format(
            sample["id"], sample["last_status"]["status"]
        )
    )

    if not ALLOWED_STATUSES_RE.match(sample["last_status"]["status"]):
        echo_warning(
            "Sample #{} has no deliverable.".format(sample_id), err=True
        )
        return

    file_types_re = re.compile("|".join(file_types), re.IGNORECASE)

    for deliverable in sample["files"]:
        if file_types and not file_types_re.match(deliverable["file_type"]):
            echo_debug("Deliverable file type is not in desired file types")
            continue

        _download_file(
            destination,
            "{}/{}".format(sample["client_id"], sample["id"]),
            deliverable["download_url"],
            skip_existing=skip_existing,
        )
