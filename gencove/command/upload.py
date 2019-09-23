"""Uploads fastq files to Gencove's system."""
import uuid
from collections import namedtuple
from datetime import datetime

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
    get_filename_from_path,
    get_s3_client_refreshable,
    login,
    seek_files_to_upload,
    upload_file,
)


UploadOptions = namedtuple(  # pylint: disable=invalid-name
    "UploadOptions", Optionals._fields + ("project_id",)
)


def upload_fastqs(source, destination, credentials, options):
    """Upload FASTQ files to Gencove's system.

    :param source: folder that contains fastq files to be uploaded.
    :type source: .fastq.gz, .fastq.bgz, .fq.gz, .fq.bgz
    :param destination: (optional) 'gncv://' notated folder
        on Gencove's system, where the files will be uploaded to.
    :type destination: str
    :param credentials: Gencove username/password to authentication.
    :type credentials: Credentials named tuple
    :param options: cli optional parameters
    :type options: UploadOptions named tuple
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
    login(api_client, credentials.email, credentials.password)
    s3_client = get_s3_client_refreshable(api_client.get_upload_credentials)
    uploads_gncv_paths = []

    for file_path in files_to_upload:
        gncv_notated_path = upload_via_file_path(
            file_path, destination, api_client, s3_client
        )
        if options.project_id:
            uploads_gncv_paths.append(gncv_notated_path)

    echo("All files were successfully uploaded.")

    if options.project_id:
        assign_samples_to_project(
            uploads_gncv_paths, options.project_id, api_client
        )


def upload_via_file_path(file_path, destination, api_client, s3_client):
    """Prepare file and upload, if it wasn't uploaded yet.

    :param file_path: a local system path to a file to be uploaded
    :type file_path: str
    :param destination: destination path in Gencove bucket. gncv notated path.
    :type destination: str
    :param api_client: instantiated Gencove api client
    :type api_client: APIClient
    :param s3_client: instantiated boto3 S3 client
    :type s3_client: boto3 s3 client

    :returns: gncv_notated_path
    """
    clean_file_path = get_filename_from_path(file_path)
    gncv_notated_path = "{}/{}".format(destination, clean_file_path)

    echo("Checking if file was already uploaded: {}".format(clean_file_path))

    upload_details = api_client.get_upload_details(gncv_notated_path)
    if upload_details["last_status"]["status"] == UPLOAD_STATUSES.done:
        echo("File was already uploaded: {}".format(clean_file_path))
        return gncv_notated_path

    echo("Uploading {} to {}".format(file_path, gncv_notated_path))
    upload_file(
        s3_client=s3_client,
        file_name=file_path,
        bucket=upload_details["s3"]["bucket"],
        object_name=upload_details["s3"]["object_name"],
    )
    return gncv_notated_path


def assign_samples_to_project(uploads_gncv_paths, project_id, api_client):
    """Assign samples to a project and trigger a run.

    :param uploads_gncv_paths: used to retrieve related unassigned samples
    :type uploads_gncv_paths: list of str
    :param project_id: samples will be assigned to this project
    :type project_id: str
    :param api_client: instantiated gencove api client
    :type api_client: APIClient
    """
    echo("Assigning uploads to project {}".format(project_id))
    samples = []
    for gncv_path in uploads_gncv_paths:
        try:
            resp = api_client.get_sample_sheet(
                gncv_path, SAMPLE_ASSIGNMENT_STATUS.unassigned
            )
        except APIClientError as err:
            echo_debug(err)
            echo_warning("Upload not found: {}".format(gncv_path))
            continue

        if not resp["results"]:
            echo_warning("Upload not found: {}".format(gncv_path))
            continue

        samples.extend(resp["results"])
        echo_debug("Sample sheet now is: {}".format(samples))

    if samples:
        echo_debug("Assigning samples to project ({})".format(project_id))
        try:
            api_client.add_samples_to_project(samples, project_id)
        except APIClientError as err:
            echo_debug(err)
            echo_warning(
                "There was an error assigning/running samples. "
                "Please try again later"
            )
