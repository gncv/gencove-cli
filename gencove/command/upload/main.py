"""Entry point into upload command."""
import json
import os
import uuid
from datetime import datetime
from time import sleep

import backoff

from gencove.client import (  # noqa: I100
    APIClientError,
    APIClientTimeout,
    APIClientTooManyRequestsError,
    CustomEncoder,
)
from gencove.command.base import Command
from gencove.command.utils import is_valid_uuid
from gencove.constants import (
    FASTQ_MAP_EXTENSION,
    SampleAssignmentStatus,
    UPLOAD_PREFIX,
)
from gencove.exceptions import ValidationError
from gencove.utils import (
    batchify,
    get_regular_progress_bar,
    get_s3_client_refreshable,
)

from .constants import (
    ASSIGN_ERROR,
    FASTQ_EXTENSIONS,
    TMP_UPLOADS_WARNING,
    UploadStatuses,
)
from .exceptions import SampleSheetError, UploadError, UploadNotFound
from .multi_file_reader import MultiFileReader
from .utils import (
    get_filename_from_path,
    get_get_upload_details_retry_predicate,
    get_gncv_path,
    parse_fastqs_map_file,
    seek_files_to_upload,
    upload_file,
    upload_multi_file,
)
from ..utils import is_valid_json
from ...constants import ASSIGN_BATCH_SIZE


# pylint: disable=too-many-instance-attributes
class Upload(Command):
    """Upload command executor."""

    # pylint: disable=too-many-arguments
    def __init__(self, source, destination, credentials, options, output, no_progress):
        super().__init__(credentials, options)
        self.source = source
        self.destination = destination
        self.project_id = options.project_id
        self.fastqs = []
        self.fastqs_map = {}
        self.upload_ids = set()
        self.output = output
        self.assigned_samples = []
        self.no_progress = no_progress
        self.metadata = options.metadata

    @staticmethod
    def generate_gncv_destination():
        """Autogenerate gencove destination path."""
        return (
            f"{UPLOAD_PREFIX}cli-"
            f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-"
            f"{uuid.uuid4().hex}"
        )

    def initialize(self):
        """Initialize upload command parameters from provided arguments."""
        self.echo_debug(f"Host is {self.options.host}")
        self.echo_warning(TMP_UPLOADS_WARNING)

        # fmt: off
        if os.path.isfile(self.source) and self.source.endswith(FASTQ_MAP_EXTENSION):  # noqa: E501  # pylint: disable=line-too-long
            self.echo_debug("Scanning fastqs map file")
            self.fastqs_map = parse_fastqs_map_file(self.source)
            self.echo_debug(f"got fastq pairs: {self.fastqs_map}")
        else:
            self.echo_debug("Seeking files to upload")
            self.fastqs = list(seek_files_to_upload(self.source))

        if not self.destination:
            self.destination = self.generate_gncv_destination()
            self.echo_info(
                f"Files will be uploaded to: {self.destination}"
            )
        # fmt: on

        # Make sure there is just one trailing slash. Only exception is
        # UPLOAD_PREFIX itself, which can have two trailing slashes.
        if self.destination != UPLOAD_PREFIX:
            self.destination = self.destination.rstrip("/")
            self.destination += "/"

        if self.is_credentials_valid:
            self.login()

    def validate(self):
        """Validate command setup before execution.

        Raises:
            ValidationError - if something is wrong with command parameters.
        """
        # fmt: off
        if self.destination and not self.destination.startswith(UPLOAD_PREFIX):
            self.echo_error(
                f"Invalid destination path. Must start with '{UPLOAD_PREFIX}'"
            )
            raise ValidationError("Bad configuration. Exiting.")
        # fmt: on

        if os.path.isfile(self.source) and not self.source.endswith(
            FASTQ_MAP_EXTENSION
        ):
            raise ValidationError(
                f"Source input ('{self.source}') is a file, "
                f"but must be a directory or a map file "
                f"('*{FASTQ_MAP_EXTENSION}'). Exiting."
            )

        if not self.fastqs and not self.fastqs_map:
            self.echo_error(
                "No FASTQ files found in the path. "
                f"Only following files are accepted: {FASTQ_EXTENSIONS}"
            )
            raise ValidationError("Bad configuration. Exiting.")

        if self.output and not self.project_id:
            raise ValidationError("--output cannot be used without --run-project-id")

        if self.metadata and not self.project_id:
            raise ValidationError("--metadata cannot be used without --run-project-id")

        if self.project_id and is_valid_uuid(self.project_id) is False:
            raise ValidationError("--run-project-id is not valid. Exiting.")

        # validate metadata json
        if self.metadata and is_valid_json(self.metadata) is False:
            raise ValidationError("--metadata is not valid JSON. Exiting.")

    def execute(self):
        """Upload fastq files from host system to Gencove cloud.

        If project id was provided, all fastq files will
        be assigned to this project, after upload.
        """
        s3_client = get_s3_client_refreshable(self.api_client.get_upload_credentials)
        try:
            if self.fastqs:
                self.upload_from_source(s3_client)
            elif self.fastqs_map:
                self.upload_from_map_file(s3_client)
        except UploadError:
            return

        self.echo_debug(f"Upload ids are now: {self.upload_ids}")
        if self.project_id:
            self.echo_debug("Cooling down period.")
            sleep(10)
            self.assign_uploads_to_project()
            if self.output:
                self.output_list()

    def upload_from_source(self, s3_client):
        """Upload command with <source> argument provided."""
        for file_path in self.fastqs:
            upload = self.upload_from_file_path(file_path, s3_client)
            if self.project_id and upload:
                self.upload_ids.add(upload.id)

        self.echo_info("All files were successfully uploaded.")

    def upload_from_map_file(self, s3_client):
        """Upload fastq files from a csv file."""
        for key, fastqs in self.fastqs_map.items():
            upload = self.concatenate_and_upload_fastqs(key, fastqs, s3_client)
            if self.project_id and upload:
                self.upload_ids.add(upload.id)

        self.echo_info("All files were successfully uploaded.")

    def concatenate_and_upload_fastqs(self, key, fastqs, s3_client):
        """Upload fastqs parts as one file."""
        client_id, r_notation = key
        self.echo_debug(
            f"Uploading fastq. client_id={client_id} r_notation={r_notation}"
        )
        self.echo_debug(f"FASTQS: {fastqs}")

        gncv_path = self.destination + get_gncv_path(client_id, r_notation)
        self.echo_debug(f"Calculated gncv path: {gncv_path}")

        upload_details = self.get_upload_details(gncv_path)

        if (
            upload_details.last_status
            and upload_details.last_status.status == UploadStatuses.DONE.value
        ):
            self.echo_info(f"File was already uploaded: {gncv_path}")
            return upload_details

        self.echo_info(f"Uploading to {gncv_path}")
        upload_multi_file(
            s3_client,
            MultiFileReader(fastqs),
            upload_details.s3.bucket,
            upload_details.s3.object_name,
            self.no_progress,
        )
        return upload_details

    def upload_from_file_path(self, file_path, s3_client):
        """Prepare file and upload, if it wasn't uploaded yet.

        Args:
            file_path (str): a local system path to a file to be uploaded.
            s3_client (boto3 s3 client): instantiated boto3 S3 client.

        Returns:
            dict representing upload details
        """
        clean_file_path = get_filename_from_path(file_path, self.source)
        self.echo_debug(f"Uploading clean file path: {clean_file_path}")
        gncv_notated_path = self.destination + clean_file_path

        self.echo_info(f"Checking if file was already uploaded: {clean_file_path}")

        try:
            upload_details = self.get_upload_details(gncv_notated_path)
        except APIClientError as err:
            if err.status_code == 400:
                self.echo_info(err.message)
                raise UploadError  # pylint: disable=W0707
            raise err

        if (
            upload_details.last_status
            and upload_details.last_status.status == UploadStatuses.DONE.value
        ):
            self.echo_info(f"File was already uploaded: {clean_file_path}")
            return upload_details

        self.echo_info(f"Uploading {file_path} to {gncv_notated_path}")
        upload_file(
            s3_client=s3_client,
            file_name=file_path,
            bucket=upload_details.s3.bucket,
            object_name=upload_details.s3.object_name,
            no_progress=self.no_progress,
        )
        return upload_details

    @backoff.on_predicate(
        backoff.expo, get_get_upload_details_retry_predicate, max_tries=10
    )
    @backoff.on_exception(backoff.expo, APIClientTooManyRequestsError, max_tries=20)
    def get_upload_details(self, gncv_path):
        """Get upload details with retry for last status update."""
        return self.api_client.get_upload_details(gncv_path)

    def assign_uploads_to_project(self):
        """Assign uploads to a project and trigger a run."""
        self.echo_info(f"Assigning uploads to project {self.project_id}")

        try:
            samples = self.build_samples(self.upload_ids)
        except (UploadError, SampleSheetError, UploadNotFound):
            self.echo_warning(ASSIGN_ERROR.format(self.project_id, self.destination))
            return

        if not samples:
            self.echo_debug("No related samples were found")
            self.echo_warning(ASSIGN_ERROR.format(self.project_id, self.destination))
            return

        self.echo_debug(f"Sample sheet now is: {samples}")

        self.echo_debug(f"Assigning samples to project ({self.project_id})")

        assigned_count = 0
        if not self.no_progress:
            progress_bar = get_regular_progress_bar(len(samples), "Assigning: ")
            progress_bar.start()
        for samples_batch in batchify(samples, batch_size=ASSIGN_BATCH_SIZE):
            try:
                samples_batch_len = len(samples_batch)
                self.echo_debug(f"Assigning batch: {samples_batch_len}")
                metadata_api = None
                if self.metadata is not None:
                    metadata_api = json.loads(self.metadata)
                assigned_batch = self.api_client.add_samples_to_project(
                    samples_batch, self.project_id, metadata_api
                )
                if assigned_batch.uploads:
                    self.assigned_samples.extend(assigned_batch.uploads)
                assigned_count += samples_batch_len
                if not self.no_progress:
                    progress_bar.update(samples_batch_len)
                self.echo_debug(f"Total assigned: {assigned_count}")
            except APIClientError as err:
                self.echo_debug(err)
                self.echo_warning("There was an error assigning/running samples.")
                if assigned_count > 0:
                    self.echo_warning(
                        "Some of the samples were assigned. "
                        "Please use the Web UI to assign "
                        "the rest of the samples"
                    )
                else:
                    self.echo_warning(
                        ASSIGN_ERROR.format(self.project_id, self.destination)
                    )
                if not self.no_progress:
                    progress_bar.finish()
                return
        if not self.no_progress:
            progress_bar.finish()
        self.echo_info("Assigned all samples to a project")

    @backoff.on_exception(
        backoff.expo, (SampleSheetError, UploadNotFound), max_time=300
    )
    def build_samples(self, uploads):
        """Get samples for current uploads.

        Returns:
            list of dict: a list of samples for the uploads.
        """
        # make a copy of uploads so as not to change the input
        search_uploads = uploads.copy()
        samples = []
        for sample_sheet in self.sample_sheet_paginator():
            if not sample_sheet:
                self.echo_debug("Sample sheet returned empty.")
                raise UploadError

            for sample in sample_sheet:
                self.echo_debug(f"Checking sample: {sample}")
                add_it = False
                if sample.fastq and sample.fastq.r1:
                    if sample.fastq.r1.upload in search_uploads:
                        add_it = True
                        search_uploads.remove(sample.fastq.r1.upload)
                        self.echo_debug(
                            f"Found sample for upload r1: {sample.fastq.r1.upload}"
                        )
                    else:
                        self.echo_debug(
                            f"R1 upload not found. sample {sample} "
                            f"uploads {search_uploads}"
                        )
                        raise UploadNotFound
                if sample.fastq and sample.fastq.r2:
                    if sample.fastq.r2.upload in search_uploads:
                        add_it = True
                        search_uploads.remove(sample.fastq.r2.upload)
                        self.echo_debug(
                            f"Found sample for upload r2: {sample.fastq.r2.upload}"
                        )
                    else:
                        self.echo_debug(
                            f"R2 upload not found. sample {sample} "
                            f"uploads {search_uploads}"
                        )
                        raise UploadNotFound

                if add_it:
                    samples.append(sample)

        if search_uploads:
            self.echo_debug(f"Have uploads without samples: {search_uploads}")
            raise SampleSheetError

        return samples

    # duplicated in projects/run_prefix/main.py with the exception difference
    def sample_sheet_paginator(self):
        """Paginate over all sample sheets for the destination.

        Yields:
            paginated lists of samples
        """
        more = True
        next_link = None
        while more:
            self.echo_debug("Get sample sheet page")
            try:
                resp = self.get_sample_sheet(next_link)
                yield resp.results
                next_link = resp.meta.next
                more = next_link is not None
            except APIClientError as err:
                self.echo_debug(err)
                raise UploadError  # pylint: disable=W0707

    @backoff.on_exception(
        backoff.expo,
        (APIClientTimeout),
        max_tries=5,
        max_time=30,
    )
    def get_sample_sheet(self, next_link=None):
        """Get samples by gncv path."""
        return self.api_client.get_sample_sheet(
            self.destination,
            SampleAssignmentStatus.UNASSIGNED.value,
            next_link,
        )

    def output_list(self):
        """Output JSON of assigning samples to a project."""
        self.echo_debug("Outputting JSON.")
        if self.output == "-":
            self.echo_data(
                json.dumps(self.assigned_samples, indent=4, cls=CustomEncoder)
            )
        else:
            dirname = os.path.dirname(self.output)
            if dirname and not os.path.exists(dirname):
                os.makedirs(dirname)
            with open(self.output, "w", encoding="utf-8") as json_file:
                json_file.write(
                    json.dumps(self.assigned_samples, indent=4, cls=CustomEncoder)
                )
            self.echo_info(f"Assigned samples response outputted to {self.output}")
