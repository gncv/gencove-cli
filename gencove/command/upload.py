"""Uploads fastq files to Gencove's system."""
import uuid
from collections import namedtuple
from datetime import datetime

import backoff

from gencove import client
from gencove.client import APIClientError
from gencove.constants import (
    FASTQ_EXTENSIONS,
    Optionals,
    SAMPLE_ASSIGNMENT_STATUS,
    TMP_UPLOADS_WARNING,
    UPLOAD_PREFIX,
    UPLOAD_STATUSES,
)
from gencove.logger import echo, echo_debug, echo_warning
from gencove.utils import (
    batchify,
    get_filename_from_path,
    get_s3_client_refreshable,
    login,
    seek_files_to_upload,
    upload_file,
)


UploadOptions = namedtuple(  # pylint: disable=invalid-name
    "UploadOptions", Optionals._fields + ("project_id",)
)
ASSIGN_ERROR = (
    "Your files were successfully uploaded, "
    "but there was an error automatically running them "
    "and assigning them to project id {}."
)


class UploadError(Exception):
    """Upload related error."""


def upload_fastqs(source, destination, credentials, options):
    """Upload FASTQ files to Gencove's system.

    Args:
        source (.fastq.gz, .fastq.bgz, .fq.gz, .fq.bgz):
            folder that contains fastq files to be uploaded.
        destination (str, optional): 'gncv://' notated folder
            on Gencove's system, where the files will be uploaded to.
        credentials (Credentials named tuple, optional):
            Gencove username/password to authentication.
        options (UploadOptions named tuple, optional): cli optional parameters.
    """
    echo_debug("Host is {}".format(options.host))

    files_to_upload = list(seek_files_to_upload(source))
    if not files_to_upload:
        echo(
            "No FASTQ files found in the path. "
            "Only following files are accepted: {}".format(FASTQ_EXTENSIONS),
            err=True,
        )
        return

    if destination and not destination.startswith(UPLOAD_PREFIX):
        echo(
            "Invalid destination path. Must start with '{}'".format(
                UPLOAD_PREFIX
            ),
            err=True,
        )
        return

    echo_warning(TMP_UPLOADS_WARNING, err=True)

    if not destination:
        destination = "{}cli-{}-{}".format(
            UPLOAD_PREFIX,
            datetime.utcnow().strftime("%Y%m%d%H%M%S"),
            uuid.uuid4().hex,
        )
        echo("Files will be uploaded to: {}".format(destination))

    api_client = client.APIClient(options.host)
    is_logged_in = login(api_client, credentials.email, credentials.password)
    if not is_logged_in:
        return

    s3_client = get_s3_client_refreshable(api_client.get_upload_credentials)
    uploads = []

    for file_path in files_to_upload:
        upload = upload_via_file_path(
            file_path, destination, api_client, s3_client
        )
        if options.project_id and upload:
            uploads.append(upload)

    echo("All files were successfully uploaded.")

    if options.project_id:
        assign_samples_to_project(
            destination, uploads, options.project_id, api_client
        )


def upload_via_file_path(  # pylint: disable=bad-continuation
    file_path, destination, api_client, s3_client
):  # noqa: D413,E501
    """Prepare file and upload, if it wasn't uploaded yet.

    Args:
        file_path (str): a local system path to a file to be uploaded.
        destination (str): destination path in Gencove bucket.
            gncv notated path.
        api_client (APIClient): instantiated Gencove api client.
        s3_client (boto3 s3 client): instantiated boto3 S3 client.

    Returns:
        dict representing upload details
    """
    clean_file_path = get_filename_from_path(file_path)
    gncv_notated_path = "{}/{}".format(destination, clean_file_path)

    echo("Checking if file was already uploaded: {}".format(clean_file_path))

    upload_details = api_client.get_upload_details(gncv_notated_path)
    if upload_details["last_status"]["status"] == UPLOAD_STATUSES.done:
        echo("File was already uploaded: {}".format(clean_file_path))
        return upload_details

    echo("Uploading {} to {}".format(file_path, gncv_notated_path))
    upload_file(
        s3_client=s3_client,
        file_name=file_path,
        bucket=upload_details["s3"]["bucket"],
        object_name=upload_details["s3"]["object_name"],
    )
    return upload_details


def get_related_sample(upload_id, sample_sheet):
    """Get sample for the upload."""
    for sample in sample_sheet:
        if (  # pylint: disable=C0330
            "r1" in sample["fastq"]
            and sample["fastq"]["r1"]["upload"] == upload_id
            or "r2" in sample["fastq"]
            and sample["fastq"]["r2"]["upload"] == upload_id
        ):
            echo_debug("Found sample for upload: {}".format(upload_id))
            return sample

    echo_debug("No sample found for upload: {}".format(upload_id))
    return None


def samples_generator(destination, api_client):
    """Paginate over all samples.

    Args:
        destination (str): gncv notated path to filter for related samples.
        api_client (APIClient): instantiated api client to use for requests.

    Yields:
        paginated lists of samples
    """
    more = True
    next_link = None
    while more:
        echo_debug("Get sample sheet page")
        try:
            resp = api_client.get_sample_sheet(
                destination, SAMPLE_ASSIGNMENT_STATUS.unassigned, next_link
            )
            yield resp["results"]
            next_link = resp["meta"]["next"]
            more = next_link is not None
        except APIClientError as err:
            echo_debug(err)
            raise UploadError


def sample_sheet_generator(destination, uploads, api_client):
    """Get samples for uploads.

    Args:
        destination (str): gncv notated path to filter for related samples.
        api_client (APIClient): instantiated api client to use for requests.
        uploads (list of dict): uploads objects from the api.

    Yields:
        Sample object
    """
    # make a copy of uploads so as not to change the input
    search_uploads = uploads[:]
    for samples in samples_generator(destination, api_client):
        if not samples:
            echo_debug("Sample sheet returned empty.")
            raise UploadError

        # for each iteration make a copy of search uploads in order to avoid
        # errors in iteration
        for upload in search_uploads[:]:
            sample = get_related_sample(upload["id"], samples)
            if sample:
                echo_debug("Found sample for upload: {}".format(upload["id"]))
                yield sample
                search_uploads.remove(upload)


@backoff.on_predicate(backoff.expo, lambda x: not x, max_tries=2)
def get_specific_sample(full_gncv_path, api_client):
    """Get sample by full gncv path."""
    return api_client.get_sample_sheet(
        full_gncv_path, SAMPLE_ASSIGNMENT_STATUS.unassigned
    )["results"]


def assign_samples_to_project(  # pylint: disable=C0330
    destination, uploads, project_id, api_client
):
    """Assign samples to a project and trigger a run.

    Args:
        destination (str): gncv notated destination. Used to retrieve related
            unassigned samples.
        uploads (list(dict)): used to select only the uploaded
            samples.
        project_id (str): samples will be assigned to this project.
        api_client (APIClient): instantiated gencove api client.
    """
    echo("Assigning uploads to project {}".format(project_id))

    try:
        samples = list(
            sample_sheet_generator(destination, uploads, api_client)
        )
    except UploadError:
        echo_warning(ASSIGN_ERROR.format(project_id))
        return

    if not samples:
        echo_debug("No related samples were found")
        echo_warning(ASSIGN_ERROR.format(project_id))
        return

    missing_uploads = []
    for upload in uploads:
        sample = get_related_sample(upload["id"], samples)
        if not sample:
            missing_uploads.append(upload)
            echo_debug("Missing sample for upload: {}".format(upload["id"]))

    for upload in missing_uploads:
        upload_samples = get_specific_sample(
            upload["destination_path"], api_client
        )
        if upload_samples:
            samples.append(upload_samples[0])
        else:
            echo_warning(ASSIGN_ERROR.format(project_id))
            return

    echo_debug("Sample sheet now is: {}".format(samples))

    if samples:
        echo_debug("Assigning samples to project ({})".format(project_id))
        for samples_batch in batchify(samples):
            try:
                api_client.add_samples_to_project(samples_batch, project_id)
            except APIClientError as err:
                echo_debug(err)
                echo_warning(
                    "There was an error assigning/running samples. "
                    "Some of the samples might have been assigned."
                )
                return
