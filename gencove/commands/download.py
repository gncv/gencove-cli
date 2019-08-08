import os
import re
import shutil

import requests

from gencove import client
from gencove.constants import ALLOWED_SAMPLE_STATUSES
from gencove.logger import echo_debug, echo_warning, echo
from gencove.utils import login


def download_file(download_to, file_prefix, url):
    """Downloads a file to file system.

    :param download_to: system/path/to/save/file/to
    :type download_to: str
    :param file_prefix: <client id>/<gencove sample id> to nest downloaded file
    under.
    :type file_prefix: str
    :param url: signed url from S3 to download the file from.
    :type url: str
    """
    with requests.get(url, stream=True) as req:
        filename = re.findall("filename=(.+)", req.headers['content-disposition'])
        file_path = os.path.join(download_to, file_prefix, filename)

        echo("Starting to download file: {}".format(file_path))

        req.raise_for_status()

        with open(file_path, 'wb') as downloaded_file:
            shutil.copyfileobj(req.raw, downloaded_file)

        echo("Finished downloading a file: {}".format(file_path))


def download_deliverables(destination, project_id, sample_ids, file_types, host, email, password):
    """Download project deliverables to a specified path on user machine.

    :param destination: path/to/save/deliverables/to.
    :type destination: str
    :param project_id: project id in Gencove's system.
    :type project_id: str
    :param sample_ids: specific samples for which to download the results.
    if not specified, download deliverables for all samples.
    :type sample_ids: list(str)
    :param file_types: specific deliverables to download results for.
    if not specified, all file types will be downloaded.
    :type file_types: list(str)
    :param host: API host to interact with.
    :type host: str
    :param email: login username
    :type email: str
    :param password: login password
    :type password: str
    """
    echo_debug("Host is {}".format(host))
    api_client = client.APIClient(host)
    login(api_client, email, password)
    if not project_id and not sample_ids:
        echo_warning("Must specify one of: project id or smaple ids", err=True)
        return

    if project_id:
        echo_debug("Retrieving sample ids for a project: {}".format(project_id))
        samples = api_client.get_project_samples(project_id)
        sample_ids = [s['id'] for s in samples]

    for sample_id in sample_ids:
        sample = api_client.get_sample_details(sample_id)
        if sample["last_status"]['status'] not in ALLOWED_SAMPLE_STATUSES:
            echo_warning("Sample #{} has no deliverable.".format(sample_id), err=True)
            continue

        for deliverable in sample['files']:
            if file_types and deliverable['file_type'] not in file_types:
                echo_debug("Deliverable file type is not in desired file types")
                continue

            download_file(destination,
                          "{}/{}".format(sample['client_id'], sample['id']),
                          deliverable['download_url'])
