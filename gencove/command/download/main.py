"""Download command executor."""
import re

import backoff

import requests

from gencove import client  # noqa: I100
from gencove.command.base import Command, ValidationError
from gencove.command.download.exceptions import DownloadTemplateError

from .constants import ALLOWED_STATUSES_RE, QC_FILE_TYPE
from .utils import (
    build_file_path,
    download_file,
    fatal_process_sample_error,
    get_download_template_format_params,
    save_qc_file,
)


class Download(Command):
    """Download command executor."""

    def __init__(self, download_to, filters, credentials, options):
        super(Download, self).__init__(credentials, options)
        self.download_to = download_to
        self.filters = filters
        self.options = options
        self.sample_ids = set()
        self.downloaded_files = set()

    def initialize(self):
        """Initialize download command."""
        if self.filters.project_id and self.filters.sample_ids:
            self.echo_debug("Bad configuration. Exiting")
            return

        self.login()

        if self.filters.project_id:
            self.echo_debug(
                "Retrieving sample ids for a project: {}".format(
                    self.filters.project_id
                )
            )

            try:
                samples_generator = self._get_paginated_samples()
                for sample in samples_generator:
                    self.sample_ids.add(sample["id"])
            except client.APIClientError:
                self.echo_warning(
                    "Project id {} not found.".format(self.filters.project_id)
                )
                return
        else:
            self.sample_ids = self.filters.sample_ids

    def validate(self):
        """Validate command configuration before execution.

        Raises:
            ValidationError : something is wrong with configuration
        """
        if not self.filters.project_id and not self.filters.sample_ids:
            self.echo_warning(
                "Must specify one of: project id or sample ids", err=True
            )
            raise ValidationError(
                "Must specify one of: project id or sample ids"
            )

        if self.filters.project_id and self.filters.sample_ids:
            self.echo_warning(
                "Must specify only one of: project id or sample ids", err=True
            )
            raise ValidationError(
                "Must specify only one of: project id or sample ids"
            )

        if not self.sample_ids:
            raise ValidationError("No samples to process. Exiting.")

        self.echo_debug(
            "Host is {} downloading to {}".format(
                self.options.host, self.download_to
            )
        )

    def execute(self):
        self.echo("Processing samples")
        for sample_id in self.sample_ids:
            try:
                self.process_sample(sample_id)
            except DownloadTemplateError:
                return

    @backoff.on_exception(
        backoff.expo,
        requests.exceptions.HTTPError,
        giveup=fatal_process_sample_error,
        max_tries=10,
    )
    def process_sample(self, sample_id):
        """Process sample.

        Check if a sample is in appropriate state and if it is,
        download its files one by one.

        If a download failed with error 403, reprocess the sample
        in order to get fresh download url.
        """
        try:
            sample = self.api_client.get_sample_details(sample_id)
        except client.APIClientError:
            self.echo_warning(
                "Sample with id {} not found. "
                "Are you using client id instead of sample id?".format(
                    sample_id
                )
            )
            return

        self.echo_debug(
            "Processing sample id {}, status {}".format(
                sample["id"], sample["last_status"]["status"]
            )
        )

        if not ALLOWED_STATUSES_RE.match(sample["last_status"]["status"]):
            self.echo_warning(
                "Sample #{} has no deliverable.".format(sample["id"]),
                err=True,
            )
            return

        file_types_re = re.compile(
            "|".join(self.filters.file_types), re.IGNORECASE
        )

        file_with_prefix = self.options.download_template.format(
            **get_download_template_format_params(
                sample["client_id"], sample["id"]
            )
        )
        self.echo_debug(
            "file path with prefix is: {}".format(file_with_prefix)
        )
        if file_types_re.match(QC_FILE_TYPE):
            self.download_sample_qc_metrics(file_with_prefix, sample_id)

        for sample_file in sample["files"]:
            # pylint: disable=C0330
            if self.filters.file_types and not file_types_re.match(
                sample_file["file_type"]
            ):
                self.echo_debug(
                    "Deliverable file type is not in desired file types"
                )
                continue

            file_path = build_file_path(
                sample_file, file_with_prefix, self.download_to
            )

            self.validate_and_download(
                file_path,
                download_file,
                file_path,
                sample_file["download_url"],
                self.options.skip_existing,
            )

    def validate_and_download(
        self, download_to_path, download_func, *args, **kwargs
    ):
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

        self.echo_debug("Adding file path: {}".format(download_to_path))
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
        qc_metrics = self.get_sample_qc_metrics(sample_id)
        file_path = build_file_path(
            dict(file_type=QC_FILE_TYPE),
            file_with_prefix,
            self.download_to,
            "qc.json",
        )

        self.validate_and_download(
            file_path, save_qc_file, file_path, qc_metrics
        )

    def _get_paginated_samples(self):
        """Generate for project samples that traverses all pages."""
        get_samples = True
        next_page = None
        while get_samples:
            self.echo_debug("Getting page: {}".format(next_page or 1))
            req = self.api_client.get_project_samples(
                self.filters.project_id, next_page
            )
            for sample in req["results"]:
                yield sample
            next_page = req["meta"]["next"]
            get_samples = next_page is not None

    def get_sample_qc_metrics(self, sample_id):
        """Retrieve sample quality control metrics.

        Args:
            sample_id(str of uuid): sample gencove id

        Returns:
            list of qc metrics.
        """
        try:
            return self.api_client.get_sample_qc_metrics(sample_id)["results"]
        except client.APIClientError:
            self.echo_warning("Error getting sample quality control metrics.")
            raise
