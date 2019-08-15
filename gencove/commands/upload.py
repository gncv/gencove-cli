"""Uploads fastq files to Gencove's system."""
import uuid
from datetime import datetime

from gencove import client
from gencove.constants import (
    FASTQ_EXTENSIONS,
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


def upload_fastqs(source, destination, host, email, password):
    """Upload FASTQ files to Gencove's system.

    :param source: folder that contains fastq files to be uploaded.
    :type source: .fastq.gz, .fastq.bgz, .fq.gz, .fq.bgz
    :param destination: (optional) 'gncv://' notated folder
        on Gencove's system, where the files will be uploaded to.
    :type destination: str
    """
    echo_debug("Host is {}".format(host))

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

    api_client = client.APIClient(host)
    login(api_client, email, password)
    s3_client = get_s3_client_refreshable(api_client.get_upload_credentials)

    for file_path in files_to_upload:
        clean_filen_path = get_filename_from_path(file_path)
        gncv_notated_path = "{}/{}".format(destination, clean_filen_path)
        echo("Uploading {} to {}".format(file_path, gncv_notated_path))

        upload_details = api_client.get_upload_details(gncv_notated_path)
        if upload_details["last_status"]["status"] == UPLOAD_STATUSES.done:
            echo("File was already uploaded: {}".format(clean_filen_path))
            continue

        upload_file(
            s3_client=s3_client,
            file_name=file_path,
            bucket=upload_details["s3"]["bucket"],
            object_name=upload_details["s3"]["object_name"],
        )

    echo("All files were successfully synced.")
