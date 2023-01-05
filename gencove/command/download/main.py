"""Download command executor."""
import json
import re

import backoff

import requests

from gencove import client  # noqa: I100
from gencove.command.base import Command
from gencove.command.download.exceptions import DownloadTemplateError
from gencove.command.utils import validate_file_types
from gencove.constants import SampleArchiveStatus
from gencove.exceptions import ValidationError

from .constants import (
    ALLOWED_ARCHIVE_STATUSES_RE,
    ALLOWED_STATUSES_RE,
    METADATA_FILE_TYPE,
    QC_FILE_TYPE,
)
from .utils import (
    build_file_path,
    download_file,
    fatal_process_sample_error,
    get_download_template_format_params,
    save_metadata_file,
    save_qc_file,
)


# pylint: disable=too-many-instance-attributes
class Download(Command):
    """Download command executor."""

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        download_to,
        filters,
        credentials,
        options,
        download_urls,
        no_progress,
        checksums,
    ):
        super().__init__(credentials, options)
        self.download_to = download_to
        self.filters = filters
        self.options = options
        self.sample_ids = set()
        self.downloaded_files = set()
        self.download_urls = download_urls
        self.download_files = []
        self.no_progress = no_progress
        self.checksums = checksums

    def initialize(self):
        """Initialize download command."""
        if self.filters.project_id and self.filters.sample_ids:
            raise ValidationError("Bad configuration. Exiting")

        self.login()

        if self.filters.project_id:
            self.echo_debug(
                f"Retrieving sample ids for a project: {self.filters.project_id}"
            )

            try:
                samples_generator = self._get_paginated_samples()
                for sample in samples_generator:
                    self.sample_ids.add(sample.id)
            except client.APIClientError as err:
                raise ValidationError(
                    f"Project id {self.filters.project_id} not found."
                ) from err
        else:
            self.sample_ids = self.filters.sample_ids

    def validate(self):
        """Validate command configuration before execution.

        Raises:
            ValidationError : something is wrong with configuration
        """
        if not self.filters.project_id and not self.filters.sample_ids:
            raise ValidationError("Must specify one of: project id or sample ids")

        if self.filters.project_id and self.filters.sample_ids:
            raise ValidationError("Must specify only one of: project id or sample ids")

        if not self.sample_ids:
            raise ValidationError("No samples to process. Exiting.")

        try:
            if self.filters.project_id:
                valid_file_types = self.api_client.get_file_types(
                    project_id=self.filters.project_id
                ).results
            else:
                valid_file_types = self.api_client.get_file_types().results
            invalid_file_types = validate_file_types(
                self.filters.file_types, valid_file_types
            )

            if invalid_file_types:
                raise ValidationError(
                    f"Invalid file types: {', '.join(invalid_file_types)}. "
                    f"Use gencove file-types command for a list of valid file types. "
                    f"Use with --project-id option to see project file types."
                )
        except client.APIClientError as err:
            self.echo_debug(err)
            self.echo_warning("There was an error while validating file types.")

        if all(
            [
                self.download_to == "-",
                not self.download_urls,
            ]
        ):
            raise ValidationError(
                "Cannot have - as a destination without download-urls."
            )

        if self.download_urls:
            self.echo_debug("Requesting download list in JSON format.")
        if self.download_to == "-":
            self.echo_debug("Will not download. Redirecting to STDOUT.")
        else:
            self.echo_debug(f"Host is {self.options.host} saving to {self.download_to}")

    def execute(self):
        if self.download_to != "-":
            self.echo_info("Processing samples")
        for sample_id in self.sample_ids:
            try:
                self.process_sample(sample_id)
            except DownloadTemplateError:
                return
        if self.download_urls:
            self.output_list()

        if all(
            [self.download_to != "-", not self.download_urls, not self.downloaded_files]
        ):
            sample_ids = [str(sample_id) for sample_id in self.sample_ids]
            self.echo_warning(
                f"Files not found for sample ids: {', '.join(sample_ids)} "
                f"and file types: {', '.join(self.filters.file_types)}."
            )

    @backoff.on_exception(
        backoff.expo,
        requests.exceptions.HTTPError,
        giveup=fatal_process_sample_error,
        max_tries=10,
    )
    @backoff.on_exception(
        backoff.expo,
        client.APIClientTooManyRequestsError,
        max_tries=20,
    )
    @backoff.on_exception(
        backoff.expo,
        client.APIClientTimeout,
        max_tries=20,
    )
    def process_sample(self, sample_id):
        """Process sample.

        Check if a sample is in appropriate state and if it is,
        get its files one by one.

        If downloading and a download failed with error 403, reprocess the
        sample in order to get fresh download url.
        """
        try:
            sample = self.api_client.get_sample_details(sample_id)
        except client.APIClientTooManyRequestsError:
            self.echo_debug(
                f"Request was throttled for sample {sample_id} "
                "because of too many requests, trying again"
            )
            raise
        except client.APIClientTimeout:
            self.echo_debug(
                f"Request was throttled for sample {sample_id} "
                "because of timeout, trying again"
            )
            raise
        except client.APIClientError:
            self.echo_warning(
                f"Sample with id {sample_id} not found. "
                "Are you using client id instead of sample id?"
            )
            return

        self.echo_debug(
            f"Processing sample id {sample.id}, status {sample.last_status.status}"
        )

        if not ALLOWED_ARCHIVE_STATUSES_RE.match(sample.archive_last_status.status):
            raise ValidationError(
                f"Sample with id {sample.id} is archived and cannot be downloaded - "
                "please restore the sample and try again."
            )

        if not ALLOWED_STATUSES_RE.match(sample.last_status.status):
            self.echo_warning(f"Sample #{sample.id} has no deliverable.")
            return

        file_types_re = re.compile("|".join(self.filters.file_types), re.IGNORECASE)

        file_with_prefix = self.options.download_template.format(
            **get_download_template_format_params(sample.client_id, sample.id)
        )
        self.echo_debug(f"file path with prefix is: {file_with_prefix}")
        if all(
            [
                self.download_to != "-",
                not self.download_urls,
                file_types_re.match(QC_FILE_TYPE),
            ]
        ):
            self.download_sample_qc_metrics(file_with_prefix, sample_id)

        if all(
            [
                self.download_to != "-",
                not self.download_urls,
                file_types_re.match(METADATA_FILE_TYPE),
            ]
        ):
            self.download_sample_metadata(file_with_prefix, sample_id)

        self.download_files.append(
            {
                "gencove_id": sample.id,
                "client_id": sample.client_id,
                "last_status": {
                    "id": sample.last_status.id,
                    "status": sample.last_status.status,
                    "created": sample.last_status.created,
                },
                "archive_last_status": {
                    "id": sample.archive_last_status.id,
                    "status": sample.archive_last_status.status,
                    "created": sample.archive_last_status.created,
                    "transition_cutoff": (sample.archive_last_status.transition_cutoff),
                },
                "files": {},
            }
        )

        for sample_file in sample.files:
            # pylint: disable=E0012,C0330
            if self.filters.file_types and not file_types_re.match(
                sample_file.file_type
            ):
                self.echo_debug("Deliverable file type is not in desired file types")
                continue

            if not self.download_urls:
                file_path = build_file_path(
                    sample_file, file_with_prefix, self.download_to
                )
                self.validate_and_download(
                    file_path,
                    download_file,
                    file_path,
                    sample_file.download_url,
                    self.options.skip_existing,
                    self.no_progress,
                )
                if self.checksums:
                    try:
                        checksum = self.api_client.get_file_checksum(sample_file.id)
                        self.create_checksum_file(file_path, checksum)
                    except client.APIClientTooManyRequestsError:
                        self.echo_debug(
                            f"Request was throttled for file {sample_file}, "
                            f"trying again"
                        )
                        raise
            self.download_files[-1]["files"][sample_file.file_type] = {
                "id": sample_file.id,
                "download_url": sample_file.download_url,
                "checksum_sha256": sample_file.checksum_sha256,
            }

    def create_checksum_file(self, file_path, checksum_sha256):
        """Create checksum file.

        Args:
            file_path (str): File path of the original file,
                will append .sha256
            checksum_sha256 (str): Checksum (sha256) value for the file

        Returns:
            None
        """
        checksum_path = f"{file_path}.sha256"
        self.echo_debug(f"Adding checksum file: {checksum_path}")
        with open(checksum_path, "w", encoding="utf-8") as checksum_file:
            checksum_file.write(checksum_sha256)

    def validate_and_download(self, download_to_path, download_func, *args, **kwargs):
        """Check if this file was already downloaded, if yes - exit.

        Args:
            download_to_path(str): system file path to donwload to
            download_func(function): function that will do the download logic
            *args: arguments that will be passed to download function
            **kwargs: keyword arguments that will be passed to download func

        Returns:
            None

        Raises:
            DownloadTemplateError: if the file was found in already downloaded
             list
        """
        if download_to_path in self.downloaded_files:
            self.echo_warning(
                "Bad template! Multiple files have the same name. "
                "Please fix the template and try again."
            )

            raise DownloadTemplateError

        download_func(*args, **kwargs)

        self.echo_debug(f"Adding file path: {download_to_path}")
        self.downloaded_files.add(download_to_path)

    def download_sample_qc_metrics(self, file_with_prefix, sample_id):
        """Download and save to file on user file system.

        Args:
            file_with_prefix(str): file path based on download template,
                prefilled with sample data
            sample_id(str of uuid): sample gencove id

        Returns:
            None
        """
        file_path = build_file_path(
            dict(file_type=QC_FILE_TYPE),
            file_with_prefix,
            self.download_to,
            f"{sample_id}_{QC_FILE_TYPE}.json",
        )

        self.validate_and_download(
            file_path,
            save_qc_file,
            file_path,
            self.api_client,
            sample_id,
            self.options.skip_existing,
        )

    def download_sample_metadata(self, file_with_prefix, sample_id):
        """Get metadata and save to file on user file system.

        Args:
            file_with_prefix(str): file path based on download template,
                prefilled with sample data
            sample_id(str of uuid): sample gencove id

        Returns:
            None
        """
        file_path = build_file_path(
            dict(file_type=METADATA_FILE_TYPE),
            file_with_prefix,
            self.download_to,
            f"{sample_id}_{METADATA_FILE_TYPE}.json",
        )

        self.validate_and_download(
            file_path,
            save_metadata_file,
            file_path,
            self.api_client,
            sample_id,
            self.options.skip_existing,
        )

    def _get_paginated_samples(self):
        """Generate for project samples that traverses all pages."""
        get_samples = True
        next_page = None
        while get_samples:
            self.echo_debug(f"Getting page: {next_page or 1}")
            req = self.api_client.get_project_samples(
                self.filters.project_id,
                next_page,
                sample_archive_status=SampleArchiveStatus.AVAILABLE.value,
            )
            for sample in req.results:
                yield sample
            next_page = req.meta.next
            get_samples = next_page is not None

    def output_list(self):
        """Output reformatted JSON of each individual sample."""
        self.echo_debug("Outputting JSON.")
        if self.download_to == "-":
            self.echo_data(
                json.dumps(self.download_files, indent=4, cls=client.CustomEncoder)
            )
        else:
            with open(self.download_to, "w", encoding="utf-8") as json_file:
                json_file.write(
                    json.dumps(
                        self.download_files,
                        indent=4,
                        cls=client.CustomEncoder,
                    )
                )
            self.echo_info(
                "Samples and their deliverables download URLs outputted to "
                f"{self.download_to}"
            )
