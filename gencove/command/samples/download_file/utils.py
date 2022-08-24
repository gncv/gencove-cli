"""Samples command utilities."""
import requests


from gencove.logger import echo_debug  # noqa: I100
from gencove.utils import get_progress_bar

from .constants import CHUNK_SIZE


def fatal_process_sample_error(err):
    """Give up retrying if the error code is different from 403.

    If the error code is 403, we need to refresh the download url and try
    processing the sample again.

    Returns:
        bool: True if to giveup on backing off, False it to continue.
    """
    return err.response.status_code != 403


def download_file(destination, download_url, no_progress=False):
    """Download a file to file system.

    Args:
        destination (File): file object
        download_url (str): url of the file to download
        no_progress (bool): don't show progress bar

    Returns:
        str : file path
            location of the downloaded file
    """
    stream_params = dict(stream=True, allow_redirects=False, headers={}, timeout=30)

    with requests.get(download_url, **stream_params) as req:
        req.raise_for_status()
        echo_debug("Starting download")

        if not no_progress:
            pbar = get_progress_bar(int(req.headers["content-length"]), "Downloading: ")
            pbar.start()
        for chunk in req.iter_content(chunk_size=CHUNK_SIZE):
            destination.write(chunk)
            if not no_progress:
                pbar.update(pbar.value + len(chunk))
        if not no_progress:
            pbar.finish()

        echo_debug("Finished downloading")
