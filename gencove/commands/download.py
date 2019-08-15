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

import requests  # noqa: I100

from tqdm import tqdm

from gencove import client  # noqa: I100
from gencove.constants import SAMPLE_STATUSES
from gencove.logger import echo, echo_debug, echo_warning
from gencove.utils import login


ALLOWED_STATUSES_RE = re.compile(
    "{}|{}".format(SAMPLE_STATUSES.succeeded, SAMPLE_STATUSES.failed),
    re.IGNORECASE,
)
FILENAME_RE = re.compile("filename=(.+)")
KILOBYTE = 1024
MEGABYTE = 1024 * KILOBYTE
NUM_MB_IN_CHUNK = 3
CHUNK_SIZE = NUM_MB_IN_CHUNK * MEGABYTE

Filters = namedtuple("Filters", ["project_id", "sample_ids", "file_types"])
Options = namedtuple("Options", ["host", "skip_existing"])


def download_deliverables(destination, filters, credentials, options):
    """Download project deliverables to a specified path on user machine.

    :param destination: path/to/save/deliverables/to.
    :type destination: str
    :param filters: allows to filter project deliverables to be downloaded
    :type filters: Filters
    :param host: API host to interact with.
    :type host: str
    :param credentials: login username/password
    :type credentials: Credentials
    :param options: different options to tweak execution
    :type options: Options
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
        samples = api_client.get_project_samples(filters.project_id)[
            "results"
        ]
        echo_debug("Found {} project samples".format(len(samples)))

        if not samples:
            echo_warning("Project has no samples to download")
            return

        for sample in samples:
            _process_sample(
                destination,
                sample["id"],
                filters.file_types,
                api_client,
                options.skip_existing,
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


def _download_file(download_to, file_prefix, url, skip_existing):
    """Download a file to file system.

    :param download_to: system/path/to/save/file/to
    :type download_to: str
    :param file_prefix: <client id>/<gencove sample id> to nest downloaded file
    under.
    :type file_prefix: str
    :param url: signed url from S3 to download the file from.
    :type url: str
    :param skip_existing: skip downloading existing files
    :type skip_existing: bool
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
        total_mb = int(total / MEGABYTE)

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
            # pylint: disable=C0330
            for chunk in tqdm(
                req.iter_content(chunk_size=CHUNK_SIZE),
                total=total_mb / NUM_MB_IN_CHUNK,
                unit="MB",
                leave=True,
                desc="Progress: ",
                unit_scale=NUM_MB_IN_CHUNK,
            ):
                downloaded_file.write(chunk)

        os.replace(file_path_tmp, file_path)
        echo("Finished downloading a file: {}".format(file_path))


def _create_filepath(download_to, file_prefix, filename):
    """Build full file path and ensure that directory structure exists.

    :param download_to: top level directory path
    :type download_to: str
    :param file_prefix: subdirectories structure to create under download_to.
    :type file_prefix: str
    :param filename: name of the file inside download_to/file_prefix structure.
    :type filename: str
    """
    path = os.path.join(download_to, file_prefix)
    os.makedirs(path, exist_ok=True)
    file_path = os.path.join(path, filename)
    echo_debug("Deduced full file path is {}".format(file_path))
    return file_path


def _get_filename(content_disposition, url):
    """Deduce filename from content disposition or url.

    :param content_disposition: Request header Content-Disposition
    :type content_disposition: str
    :param url: URL string
    :type url: str
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
    sample = api_client.get_sample_details(sample_id)
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
