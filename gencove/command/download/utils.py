"""Download command utilities."""
import json
import os
import re
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import parse_qs, urlparse

import backoff

from pydantic import HttpUrl

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
    MEGABYTE,
)

MAX_PARALLEL_DOWNLOADS = 8
MIN_BYTES_PER_PART = 8 * MEGABYTE  # 8 MB


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
        url (str or HttpUrl): URL string or HttpUrl object

    Returns:
        str: filename
    """
    url_str = str(url)
    try:
        filename = re.findall(
            FILENAME_RE,
            parse_qs(urlparse(url_str).query)["response-content-disposition"][0],
        )[0]
    except (KeyError, IndexError):
        echo_debug(
            "URL didn't contain filename query argument. Assume filename from url"
        )
        filename = urlparse(url_str).path.split("/")[-1]

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
    download_url = (
        str(download_url) if isinstance(download_url, HttpUrl) else download_url
    )
    file_path_tmp = f"{file_path}.tmp"
    request_kwargs_base = {"stream": True, "allow_redirects": False, "timeout": 30}

    response = requests.get(download_url, **request_kwargs_base)

    try:
        response.raise_for_status()
        total = _extract_total_size(response.headers)

        if (
            skip_existing
            and os.path.isfile(file_path)
            and os.path.getsize(file_path) == total
        ):
            echo_info(f"Skipping existing file: {file_path}")
            return file_path

        echo_info(f"Downloading file to {file_path}")
        worker_count = _determine_parallel_workers(total)

        echo_debug(f"Using {worker_count} worker(s)")

        if worker_count == 1:
            # For small files or limited threads, consume the initial response stream
            # instead of making additional range requests.
            # this is primarily to maintain compatibility with older tests
            _download_from_response(response, file_path_tmp, total, no_progress)
        else:
            with open(file_path_tmp, "wb") as tmp_file:
                tmp_file.truncate(total)

            response.close()
            _download_in_parallel(
                download_url,
                file_path_tmp,
                total,
                worker_count,
                no_progress,
                request_kwargs_base,
            )
        _finalize_download(file_path_tmp, file_path)
        echo_info(f"Finished downloading file: {file_path}")
        return file_path
    finally:
        response.close()

        # if there's a failure, tmp file remains
        # this ensures it is always removed
        if os.path.exists(file_path_tmp):
            echo_info(f"Removing temporary file: {file_path_tmp}")
            os.remove(file_path_tmp)


def _download_from_response(response, file_path_tmp, total, no_progress):
    """Download file by consuming response stream

    Args:
        response (requests.Response): Active streaming response object
        file_path_tmp (str): Temporary file path used during download
        total (int): Full size of the object in bytes
        no_progress (bool): Disable progress reporting when True

    Returns:
        None
    """
    progress = 0
    pbar = None
    if not no_progress:
        pbar = get_progress_bar(total, "Downloading: ")
        pbar.start()

    with open(file_path_tmp, "wb") as downloaded_file:
        for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
            if not chunk:
                continue
            downloaded_file.write(chunk)
            progress += len(chunk)
            if pbar:
                pbar.update(progress)

    if pbar:
        pbar.finish()


def _download_in_parallel(  # pylint: disable=too-many-locals
    download_url,
    file_path_tmp,
    total,
    worker_count,
    no_progress,
    request_kwargs_base,
):
    """Download file by splitting into byte ranges and fetching in parallel

    Args:
        download_url (str): URL of the object to download
        file_path_tmp (str): Temporary file path used during download
        total (int): Full size of the object in bytes
        worker_count (int): Number of concurrent range requests
        no_progress (bool): Disable progress reporting when True
        request_kwargs_base (dict): Common keyword arguments for `requests.get`

    Returns:
        None
    """
    if not os.path.exists(file_path_tmp):
        with open(file_path_tmp, "wb") as tmp_file:
            tmp_file.truncate(total)

    pbar = None
    progress = _ThreadSafeCounter()
    cancel_event = threading.Event()

    if not no_progress:
        pbar = get_progress_bar(total, "Downloading: ")
        pbar.start()

    def update_progress(amount):
        if not pbar:
            return
        current = progress.increment(amount)
        pbar.update(current)

    def fetch_range(start, end):
        """Fetch range of bytes from the download URL and write to file"""
        if cancel_event.is_set():
            return
        expected = end - start + 1
        request_headers = {"Range": f"bytes={start}-{end}"}
        request_kwargs = request_kwargs_base
        request_kwargs["headers"] = request_headers
        with requests.get(download_url, **request_kwargs) as resp:
            resp.raise_for_status()
            bytes_written = 0
            with open(file_path_tmp, "rb+") as part_file:
                part_file.seek(start)
                for chunk in resp.iter_content(chunk_size=CHUNK_SIZE):
                    if cancel_event.is_set():
                        return
                    if not chunk:
                        continue
                    part_file.write(chunk)
                    bytes_written += len(chunk)
                    update_progress(len(chunk))
            if bytes_written != expected:
                raise requests.exceptions.ContentDecodingError(
                    f"Incomplete range download for bytes {start}-{end} "
                    f"(expected {expected}, got {bytes_written})"
                )

    ranges = _build_ranges(total, worker_count)
    executor = ThreadPoolExecutor(max_workers=worker_count)
    futures = [executor.submit(fetch_range, start, end) for start, end in ranges]
    try:
        for future in as_completed(futures):
            future.result()
    except KeyboardInterrupt:
        cancel_event.set()
        for future in futures:
            future.cancel()
        executor.shutdown(wait=False)
        raise
    finally:
        executor.shutdown(wait=True)

    if pbar:
        pbar.finish()


def _determine_parallel_workers(total):
    """Determine how many workers to use based on object size

    Args:
        total (int): Full size of the object in bytes

    Returns:
        int: Number of workers to spawn
    """
    parts = max(1, (total + MIN_BYTES_PER_PART - 1) // MIN_BYTES_PER_PART)
    return min(MAX_PARALLEL_DOWNLOADS, parts)


def _build_ranges(total, worker_count):
    """Return a list of (start, end) byte ranges for the download

    Args:
        total (int): Full size of the object in bytes
        worker_count (int): Number of ranges to generate

    Returns:
        list[tuple[int, int]]: Inclusive byte ranges for each worker
    """
    part_size = (total + worker_count - 1) // worker_count
    ranges = []
    for index in range(worker_count):
        start = index * part_size
        end = min(start + part_size, total) - 1
        if start > end:
            break
        ranges.append((start, end))
    return ranges


def _finalize_download(file_path_tmp, file_path):
    """Replace destination file with freshly downloaded temp file

    Args:
        file_path_tmp (str): Path to the partially downloaded file
        file_path (str): Final destination path for the download

    Returns:
        None
    """
    if os.path.exists(file_path):
        echo_debug(f"Found old file under same name: {file_path}. Removing it.")
        os.remove(file_path)
    os.rename(file_path_tmp, file_path)


# pylint: disable=too-few-public-methods
class _ThreadSafeCounter:
    """Thread safe counter to track aggregate progress"""

    def __init__(self):
        self.value = 0
        self._lock = threading.Lock()

    def increment(self, amount):
        """Increase counter by amount and return new total

        Args:
            amount (int): Number of bytes to add to the counter

        Returns:
            int: Updated total
        """
        with self._lock:
            self.value += amount
            return self.value


def _extract_total_size(headers):
    """Determine total size of the object based on response headers

    Args:
        headers (Mapping[str, str]): Response headers returned by S3

    Returns:
        int: Total size of the object in bytes
    """
    if "content-range" in headers:
        # format: bytes start-end/total
        _, _, total_str = headers["content-range"].partition("/")
        return int(total_str)
    length = int(headers["content-length"])
    return length


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
    return err.response.status_code not in [403, 500, 502, 503, 504]


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
