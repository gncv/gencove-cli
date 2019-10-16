"""Entry point into upload command."""
import uuid
from collections import namedtuple
from datetime import datetime
from time import sleep

import backoff

import requests

from gencove.client import APIClientError  # noqa: I100
from gencove.command.base import Command, ValidationError
from gencove.constants import Optionals, SAMPLE_ASSIGNMENT_STATUS
from gencove.utils import (
    batchify,
    get_filename_from_path,
    get_regular_progress_bar,
    get_s3_client_refreshable,
    login,
)

from .constants import (
    FASTQ_EXTENSIONS,
    TMP_UPLOADS_WARNING,
    UPLOAD_PREFIX,
    UPLOAD_STATUSES,
)
from .utils import (
    get_get_upload_details_retry_predicate,
    get_related_sample,
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
ASSIGN_BATCH_SIZE = 200


class UploadError(Exception):
    """Upload related error."""


class SampleSheetError(Exception):
    """Error to generate the sample sheet for uploads."""


class Upload(Command):
    """Upload command executor."""

    def __init__(self, source, destination, credentials, options):
        super(Upload, self).__init__(credentials, options)
        self.source = source
        self.destination = destination
        self.project_id = options.project_id
        self.fastqs = []
        self.upload_ids = set()

    @staticmethod
    def generate_gncv_destination():
        """Autogenerate gencove destination path."""
        return "{}cli-{}-{}".format(
            UPLOAD_PREFIX,
            datetime.utcnow().strftime("%Y%m%d%H%M%S"),
            uuid.uuid4().hex,
        )

    def initialize(self):
        """Initialize upload command parameters from provided arguments."""
        self.echo_debug("Host is {}".format(self.options.host))
        self.echo_warning(TMP_UPLOADS_WARNING, err=True)

        self.fastqs = list(seek_files_to_upload(self.source))

        if not self.destination:
            self.destination = self.generate_gncv_destination()
            self.echo(
                "Files will be uploaded to: {}".format(self.destination)
            )

        self.is_logged_in = login(
            self.api_client, self.credentials.email, self.credentials.password
        )

    def validate(self):
        """Validate command setup before execution.

        Raises:
            ValidationError - if something is wrong with command parameters.
        """
        if self.destination and not self.destination.startswith(
            UPLOAD_PREFIX  # pylint: disable=C0330
        ):
            self.echo(
                "Invalid destination path. Must start with '{}'".format(
                    UPLOAD_PREFIX
                ),
                err=True,
            )
            raise ValidationError("Bad configuration. Exiting.")

        if not self.fastqs:
            self.echo(
                "No FASTQ files found in the path. "
                "Only following files are accepted: {}".format(
                    FASTQ_EXTENSIONS
                ),
                err=True,
            )
            raise ValidationError("Bad configuration. Exiting.")

        if not self.is_logged_in:
            raise ValidationError("User must login. Exiting.")

    def execute(self):
        """Upload fastq files from host system to Gencove cloud.

        If project id was provided, all fastq files will
        be assigned to this project, after upload.
        """
        s3_client = get_s3_client_refreshable(
            self.api_client.get_upload_credentials
        )

        for file_path in self.fastqs:
            upload = self.upload_from_file_path(file_path, s3_client)
            if self.project_id and upload:
                self.upload_ids.add(upload["id"])

        self.echo("All files were successfully uploaded.")

        if self.project_id:
            self.echo_debug("Cooling down period.")
            sleep(10)
            self.assign_uploads_to_project()

    def upload_from_file_path(self, file_path, s3_client):
        """Prepare file and upload, if it wasn't uploaded yet.

        Args:
            file_path (str): a local system path to a file to be uploaded.
            s3_client (boto3 s3 client): instantiated boto3 S3 client.

        Returns:
            dict representing upload details
        """
        clean_file_path = get_filename_from_path(file_path)
        gncv_notated_path = "{}/{}".format(self.destination, clean_file_path)

        self.echo(
            "Checking if file was already uploaded: {}".format(
                clean_file_path
            )
        )

        upload_details = self.get_upload_details(gncv_notated_path)
        if upload_details["last_status"]["status"] == UPLOAD_STATUSES.done:
            self.echo("File was already uploaded: {}".format(clean_file_path))
            return upload_details

        self.echo("Uploading {} to {}".format(file_path, gncv_notated_path))
        upload_file(
            s3_client=s3_client,
            file_name=file_path,
            bucket=upload_details["s3"]["bucket"],
            object_name=upload_details["s3"]["object_name"],
        )
        return upload_details

    @backoff.on_predicate(
        backoff.expo, get_get_upload_details_retry_predicate, max_tries=10
    )
    def get_upload_details(self, gncv_path):
        """Get upload details with retry for last status update."""
        return self.api_client.get_upload_details(gncv_path)

    def assign_uploads_to_project(self):
        """Assign uploads to a project and trigger a run."""
        self.echo("Assigning uploads to project {}".format(self.project_id))

        try:
            samples = list(self.samples_generator(self.upload_ids))
        except (UploadError, SampleSheetError):
            self.echo_warning(ASSIGN_ERROR.format(self.project_id))
            return

        if not samples:
            self.echo_debug("No related samples were found")
            self.echo_warning(ASSIGN_ERROR.format(self.project_id))
            return

        self.echo_debug("Sample sheet now is: {}".format(samples))

        self.echo_debug(
            "Assigning samples to project ({})".format(self.project_id)
        )

        assigned_count = 0
        progress_bar = get_regular_progress_bar(len(samples), "Assigning: ")
        progress_bar.start()
        for samples_batch in batchify(samples, batch_size=ASSIGN_BATCH_SIZE):
            try:
                samples_batch_len = len(samples_batch)
                self.echo_debug(
                    "Assigning batch: {}".format(samples_batch_len)
                )
                self.api_client.add_samples_to_project(
                    samples_batch, self.project_id
                )
                assigned_count += samples_batch_len
                progress_bar.update(samples_batch_len)
                self.echo_debug("Total assigned: {}".format(assigned_count))
            except APIClientError as err:
                self.echo_debug(err)
                self.echo_warning(
                    "There was an error assigning/running samples."
                )
                if assigned_count > 0:
                    self.echo_warning(
                        "Some of the samples were assigned. "
                        "Please use the Web UI to assign "
                        "the rest of the samples"
                    )
                else:
                    self.echo_warning(
                        "You can retry assignment without uploading again "
                        "via upload command using "
                        "destination: {}".format(self.destination)
                    )
                progress_bar.finish()
                return
        progress_bar.finish()
        self.echo("Assigned all samples to a project")

    @backoff.on_exception(backoff.expo, SampleSheetError, max_time=300)
    def samples_generator(self, uploads):
        """Get samples for current uploads.

        Yields:
            Sample object
        """
        # make a copy of uploads so as not to change the input
        search_uploads = set(uploads)
        for samples in self.sample_sheet_paginator():
            if not samples:
                self.echo_debug("Sample sheet returned empty.")
                raise UploadError

            # for each iteration make a copy of search uploads
            # in order to avoid errors in iteration
            for uid in set(search_uploads):
                sample, r1_uid, r2_uid = get_related_sample(uid, samples)
                if sample:
                    self.echo_debug("Found sample for upload: {}".format(uid))
                    yield sample
                    if r1_uid and r1_uid in search_uploads:
                        search_uploads.remove(r1_uid)
                    if r2_uid and r2_uid in search_uploads:
                        search_uploads.remove(r2_uid)

        if search_uploads:
            self.echo_debug(
                "Have uploads without samples: {}".format(search_uploads)
            )
            raise SampleSheetError

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
                yield resp["results"]
                next_link = resp["meta"]["next"]
                more = next_link is not None
            except APIClientError as err:
                self.echo_debug(err)
                raise UploadError

    @backoff.on_exception(
        backoff.expo,
        (requests.exceptions.ConnectionError, requests.exceptions.Timeout),
        max_tries=5,
        max_time=30,
    )
    def get_sample_sheet(self, next_link=None):
        """Get samples by gncv path."""
        return self.api_client.get_sample_sheet(
            self.destination, SAMPLE_ASSIGNMENT_STATUS.unassigned, next_link
        )
