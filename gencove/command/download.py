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
from gencove.constants import (
    Optionals,
    SAMPLE_STATUSES,
    DownloadTemplateParts,
)
from gencove.logger import echo, echo_debug, echo_warning
from gencove.utils import (
    get_progress_bar,
    login,
    get_filename_from_download_url,
    deliverable_type_from_filename,
)

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
    "DownloadOptions",
    Optionals._fields + ("skip_existing", "download_template"),
)

# todo remember already downloaded paths and if we meet same downloadabe again - fail due to error in a template
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
    is_logged_in = login(api_client, credentials.email, credentials.password)
    if not is_logged_in:
        return

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
                    destination, sample["id"], api_client, filters, options
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
        _process_sample(destination, sample_id, api_client, filters, options)


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


def _download_file(download_to, file_prefix, deliverable, options):
    """Download a file to file system.

    Args:
        download_to (str): system/path/to/save/file/to
        file_prefix (str): <client id>/<gencove sample id> to nest downloaded
            file.
        deliverable (dict): file object from api.
        options (:obj:`tuple` of type DownloadOptions):
            contains additional flags for download processing.
    """
    echo_debug(
        "Downloading file to {} with prefix {}".format(
            download_to, file_prefix
        )
    )
    prefix_parts = file_prefix.split("/")
    filename_prefix = prefix_parts[-1]
    dirs_prefix = "/".join(prefix_parts[:-1])
    with requests.get(deliverable["download_url"], stream=True) as req:
        req.raise_for_status()
        source_filename = get_filename_from_download_url(
            req.headers["content-disposition"], deliverable["download_url"]
        )
        destination_filename = "{}.{}".format(
            filename_prefix, deliverable_type_from_filename(source_filename)
        )
        filename_tmp = "download-{}.tmp".format(uuid.uuid4().hex)
        file_path = _create_filepath(
            download_to, dirs_prefix, destination_filename
        )
        file_path_tmp = _create_filepath(
            download_to, file_prefix, filename_tmp
        )
        total = int(req.headers["content-length"])
        # todo refactor destination filename deduction to outside of this func based on deliverable from sample details
        # todo move skip existing check to outside of download file func
        # todo on the same par as skip existing, remember downloaded files and do todo on line 43
        # pylint: disable=C0330
        if (
            options.skip_existing
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
        file_prefix (str): subdirectories structure to create under
            download_to.
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


# pylint: disable=C0330
def _process_sample(destination, sample_id, api_client, filters, options):
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
            "Sample #{} has no deliverable.".format(sample["id"]), err=True
        )
        return

    file_types_re = re.compile("|".join(filters.file_types), re.IGNORECASE)
    file_prefix = options.download_template.format(
        **{
            DownloadTemplateParts.client_id: sample["client_id"],
            DownloadTemplateParts.gencove_id: sample["id"],
        }
    )

    for deliverable in sample["files"]:
        if filters.file_types and not file_types_re.match(
            deliverable["file_type"]
        ):
            echo_debug("Deliverable file type is not in desired file types")
            continue

        _download_file(destination, file_prefix, deliverable, options)
