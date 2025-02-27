"""Utils for upload command."""
import csv
import os
import platform
import re
import urllib.parse
from collections import defaultdict
from urllib.parse import urlparse

from boto3.s3.transfer import TransferConfig

from botocore.exceptions import ClientError

from gencove.client import APIClientError
from gencove.exceptions import ValidationError
from gencove.logger import echo_debug, echo_info
from gencove.utils import CHUNK_SIZE, get_progress_bar

from .constants import (
    FASTQ_EXTENSIONS,
    FastQ,
    PATH_TEMPLATE,
    PathTemplateParts,
    R_NOTATION_MAP,
)


def upload_file(
    s3_client, file_name, bucket, object_name=None, no_progress=False
):  # noqa: D413
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
        if not no_progress:
            progress_bar = get_progress_bar(os.path.getsize(file_name), "Uploading: ")
            progress_bar.start()
        s3_client.upload_file(
            file_name,
            bucket,
            object_name,
            Config=config,
            Callback=_progress_bar_update(progress_bar) if not no_progress else None,
        )
        if not no_progress:
            progress_bar.finish()
    except ClientError as err:
        echo_info(f"Failed to upload file {file_name}: {err}")
        return False
    return True


def upload_multi_file(
    s3_client,
    file_obj,
    bucket,
    object_name=None,  # pylint: disable=E0012,C0330
    no_progress=False,
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

        if not no_progress:
            progress_bar = get_progress_bar(file_obj.get_size(), "Uploading: ")
            progress_bar.start()
        s3_client.upload_fileobj(
            file_obj,
            bucket,
            object_name,
            Config=config,
            Callback=_progress_bar_update(progress_bar) if not no_progress else None,
        )
        if not no_progress:
            progress_bar.finish()
    except ClientError as err:
        echo_info(f"Failed to upload file {file_obj.name}: {err}")
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
                echo_debug(f"Found file to upload: {file_path}")
                yield file_path

        dirs.sort()
        for folder in dirs:
            seek_files_to_upload(folder, root)


def get_get_upload_details_retry_predicate(resp):
    """Triggers retry if upload details came back without last status."""
    return not resp.last_status


def get_upload_details_give_up_predicate(exc: APIClientError):
    """
    Decide if we should give up trying to get upload details when exception
    is raised.

    Args:
        exc (APIClientError): Exception raised.

    Returns:
        bool: True for giving up, False to continue.
    """
    return exc.status_code in [400]


def get_filename_from_path(full_path, source):
    """Cross OS get file name utility."""
    relpath = os.path.relpath(os.path.normpath(full_path), start=source)
    if platform.system() == "Windows":
        return relpath.replace("\\", "/")
    return relpath


def _validate_fastq(fastq):
    """Validate fastq object.

    Args:
        fastq (FastQ): fastq object
    Returns:
        None if all good
    Raises:
        ValidationError if fastq is not valid
    """
    if looks_like_url(fastq.path):
        if not valid_fastq_file_name_in_url(fastq.path):
            raise ValidationError(
                f"Could not determine FASTQ file name from supplied URL {fastq.path}"
            )
    else:
        if not fastq.path.lower().endswith(FASTQ_EXTENSIONS):
            echo_info(f"Unsupported file type found: {fastq.path}")
            raise ValidationError(f"Bad file extension in path: {fastq.path}")
        if not os.path.exists(fastq.path):
            echo_info(f"Path does not exist: {fastq.path}")
            raise ValidationError(f"Could not find: {fastq.path}")

    if "_" in fastq.client_id:
        echo_info("Underscore is not allowed in client id")
        raise ValidationError("Underscore is not allowed in client id")
    if fastq.r_notation not in R_NOTATION_MAP:
        echo_info(f"Wrong R notation: {fastq.r_notation}")
        echo_info(f"Valid R notations are: {R_NOTATION_MAP.keys()}")
        raise ValidationError(f"Wrong R notation: {fastq.r_notation}")


def _validate_header(header):
    header_columns = [header_item.strip().lower() for header_item in header.values()]
    for column in FastQ.model_fields:
        if column not in header_columns:
            raise ValidationError(
                f"Unexpected CSV header. Expected: {', '.join(FastQ.model_fields)}"
            )


def _validate_parsed_map(fastqs: dict):
    """Validates contents of fastqs dict to ensure path
    column contains homogenous values, i.e. all local paths
     or all URLs"""
    paths = [next(iter(x)) for x in fastqs.values()]
    all_urls = all(looks_like_url(p) for p in paths)
    all_paths = all(not looks_like_url(p) for p in paths)
    if not all_urls and not all_paths:
        raise ValidationError(
            "Detected both URLs and file paths in 'path' column. "
            "Please only supply one type of path (URL or local path)"
            " in the map file."
        )


def parse_fastqs_map_file(fastqs_map_path):
    """Parse fastq map file.

    Map file has to have following columns/headers:
        client_id, r_notation, path

    Note this map file also supports URLs under the path column

    Example fastqs map file:
        client_id,r_notation,path
        sample1,R1,dir1/sample1_L001_R1.fastq.gz
        sample1,R1,dir1/sample1_L002_R1.fastq.gz
        sample2,R2,dir2/sample1_L001_R2.fastq.gz

    Args:
        fastqs_map_path (str): path to CSV file

    Returns:
        defaultdict: map of fastq file to samples
            {
                (<client_id>, <r_notation>): [path1, path2, ...],
            }
    """
    fastqs = defaultdict(list)
    with open(fastqs_map_path, encoding="utf-8") as fastqs_file:
        reader = csv.DictReader(fastqs_file, fieldnames=FastQ.__fields__)
        # read headers row
        header = next(reader)
        _validate_header(header)
        for row in reader:
            fastq = FastQ(**row)
            _validate_fastq(fastq)
            fastqs[(fastq.client_id, R_NOTATION_MAP[fastq.r_notation])].append(
                fastq.path
            )
    _validate_parsed_map(fastqs)
    return fastqs


def get_gncv_path(client_id, r_notation):
    """Build gncv upload path.

    Args:
        client_id (str): sample client id
        r_notation (str): upload R1/2 notation

    Returns:
        str: gncv upload path
    """
    return PATH_TEMPLATE.format(
        **{
            PathTemplateParts.client_id.value: client_id,
            PathTemplateParts.r_notation.value: r_notation,
        }
    )


def looks_like_url(value):
    """Detects if input value appears to be a URL

    Args:
        value (str): value to test

    Returns:
        bool: True if URL-like, False otherwise
    """
    try:
        result = urlparse(value)
        if result.scheme in ["http", "https"]:
            if result.netloc:
                return True
    except ValueError:
        return False
    return False


def valid_fastq_file_name_in_url(value):
    """Attempt to detect FASTQ file name in URL"""
    path = urllib.parse.urlparse(value).path
    fastq_extensions_regex = [x.replace(".", r"\.") for x in FASTQ_EXTENSIONS]
    re_fastq_extensions = "|".join(fastq_extensions_regex)
    re_pattern = rf"/([^/]*?({re_fastq_extensions}))$"
    match = re.search(re_pattern, path)
    if match:
        return True
    return False
