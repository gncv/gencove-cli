"""Utils for upload command."""
import os

import backoff

from boto3.s3.transfer import TransferConfig

from botocore.exceptions import ClientError

from gencove.constants import SAMPLE_ASSIGNMENT_STATUS
from gencove.logger import echo, echo_debug
from gencove.utils import CHUNK_SIZE, get_progress_bar

from .constants import FASTQ_EXTENSIONS


def upload_file(s3_client, file_name, bucket, object_name=None):  # noqa: D413
    """Upload a file to an S3 bucket.

    Args:
        s3_client: Boto s3 client.
        file_name (str): File to upload.
        bucket (str): Bucket to upload to.
        object_name (str): S3 object name.
            If not specified then file_name is used

    Returns:
        True if file was uploaded, else False
    """
    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = file_name

    # Upload the file
    try:
        # Set desired multipart threshold value of 5GB
        config = TransferConfig(
            multipart_threshold=CHUNK_SIZE,
            multipart_chunksize=CHUNK_SIZE,
            use_threads=True,
            max_concurrency=10,
        )

        progress_bar = get_progress_bar(
            os.path.getsize(file_name), "Uploading: "
        )
        progress_bar.start()
        s3_client.upload_file(
            file_name,
            bucket,
            object_name,
            Config=config,
            Callback=_progress_bar_update(progress_bar),
        )
        progress_bar.finish()
    except ClientError as err:
        echo("Failed to upload file {}: {}".format(file_name, err), err=True)
        return False
    return True


def _progress_bar_update(pbar):  # noqa: D413
    """Update progress bar manually.

    Helper method for S3 Transfer,
    which needs a callback to update the progressbar.

    Args:
        pbar: progressbar.ProgressBar instance

    Returns:
        a function that in turn accepts chunk that is used to update the
        progressbar.
    """
    # noqa: D202
    def _update_pbar(chunk_uploaded_in_bytes):
        pbar.update(pbar.value + chunk_uploaded_in_bytes)

    return _update_pbar


def seek_files_to_upload(path, path_root=""):
    """Generate a list of valid fastq files."""
    for root, dirs, files in os.walk(path):
        files.sort()
        for file in files:
            file_path = os.path.join(path_root, root, file)

            if file_path.lower().endswith(FASTQ_EXTENSIONS):
                echo_debug("Found file to upload: {}".format(file_path))
                yield file_path

        dirs.sort()
        for folder in dirs:
            seek_files_to_upload(folder, root)


@backoff.on_predicate(backoff.expo, lambda x: not x, max_tries=5)
def get_specific_sample(full_gncv_path, api_client):
    """Get sample by full gncv path."""
    return api_client.get_sample_sheet(
        full_gncv_path, SAMPLE_ASSIGNMENT_STATUS.unassigned
    )["results"]


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
