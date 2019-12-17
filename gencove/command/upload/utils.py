"""Utils for upload command."""
import csv
import os
import platform
from collections import defaultdict

from boto3.s3.transfer import TransferConfig

from botocore.exceptions import ClientError

from gencove.command.base import ValidationError
from gencove.logger import echo, echo_debug
from gencove.utils import CHUNK_SIZE, get_progress_bar

from .constants import FASTQ_EXTENSIONS, FastQ, R_NOTATION_MAP


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


def upload_multi_file(
    s3_client, file_obj, bucket, object_name=None  # pylint: disable=C0330
):  # noqa: D413
    """Upload a file to an S3 bucket.

    Args:
        s3_client: Boto s3 client.
        file_obj (MultiFileReader): File-like object with read() and
            __iter__ methods
        bucket (str): Bucket to upload to.
        object_name (str): S3 object name.
            If not specified then file_name is used

    Returns:
        True if file was uploaded, else False
    """
    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = file_obj.name

    # Upload the file
    try:
        # Set desired multipart threshold value of 5GB
        config = TransferConfig(
            multipart_threshold=CHUNK_SIZE,
            multipart_chunksize=CHUNK_SIZE,
            use_threads=True,
            max_concurrency=10,
        )

        progress_bar = get_progress_bar(file_obj.get_size(), "Uploading: ")
        progress_bar.start()
        s3_client.upload_fileobj(
            file_obj,
            bucket,
            object_name,
            Config=config,
            Callback=_progress_bar_update(progress_bar),
        )
        progress_bar.finish()
    except ClientError as err:
        echo(
            "Failed to upload file {}: {}".format(file_obj.name, err),
            err=True,
        )
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


def get_get_upload_details_retry_predicate(resp):
    """Triggers retry if upload details came back without last status."""
    return not resp["last_status"]


def get_filename_from_path(full_path, source):
    """Cross OS get file name utility."""
    relpath = os.path.relpath(os.path.normpath(full_path), start=source)
    if platform.system() == "Windows":
        return relpath.replace("\\", "/")
    return relpath


def parse_fastqs_map_file(fastqs_map_path):
    """Parse fastq map file.

    Map file has to have following columns/headers:
        batch, client_id, r_notation, path

    Example fastqs map file:
        batch,client_id,r_notation,path
        dir1,sample1,R1,dir1/sample1_L001_R1.fastq.gz
        dir1,sample1,R1,dir1/sample1_L002_R1.fastq.gz
        dir2,sample2,R2,dir2/sample1_L001_R2.fastq.gz

    Args:
        fastqs_map_path (str): path to CSV file

    Returns:
        defaultdict: map of fastq file to samples
            {
                (<batch>, <client_id>, <r_notation>): [path1, path2, ...],
            }
    """
    fastqs = defaultdict(list)
    with open(fastqs_map_path) as fastqs_file:
        reader = csv.DictReader(fastqs_file, fieldnames=FastQ._fields)
        # read headers row
        _ = next(reader)
        for row in reader:
            fastq = FastQ(**row)
            if not fastq.path.lower().endswith(FASTQ_EXTENSIONS):
                raise ValidationError(
                    "Bad file extension in path: {}".format(fastq.path)
                )

            fastqs[
                (
                    fastq.batch,
                    fastq.client_id,
                    R_NOTATION_MAP[fastq.r_notation],
                )
            ].append(fastq.path)
    return fastqs
