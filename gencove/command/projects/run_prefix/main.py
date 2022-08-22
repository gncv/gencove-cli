"""Assign uploads from a prefix to a project subcommand."""

import json

import backoff

from ...base import Command
from ...utils import is_valid_json, is_valid_uuid
from .... import client
from ....constants import ASSIGN_BATCH_SIZE, UPLOAD_PREFIX
from ....exceptions import ValidationError
from ....utils import batchify


class RunPrefix(Command):
    """Run prefix command executor."""

    def __init__(self, project_id, prefix, credentials, options):
        super().__init__(credentials, options)
        self.project_id = project_id
        self.prefix = prefix
        self.metadata_json = options.metadata_json
        self.status = options.status

    def initialize(self):
        """Initialize run-prefix subcommand."""
        self.login()

    def validate(self):
        """Validate command input.

        Raises:
            ValidationError - if something is wrong with command parameters.
        """
        if is_valid_uuid(self.project_id) is False:
            raise ValidationError("Project ID is not valid. Exiting.")
        if self._valid_prefix() is False:
            raise ValidationError("Prefix is not valid. Exiting.")
        if self.metadata_json and is_valid_json(self.metadata_json) is False:
            raise ValidationError("Metadata JSON is not valid. Exiting.")

    def execute(self):
        """Assign samples to the project from the prefixed path."""
        try:
            self.echo_debug(f"Retrieving sample sheet: search_term={self.prefix}")
            samples = []
            self.echo_info("Gathering uploads.")
            for sample_sheet in self._get_paginated_sample_sheet():
                if not sample_sheet:
                    raise ValidationError("No matching paths found.")
                samples.extend(sample_sheet)
            self._assign_samples(samples)
            self.echo_info(
                "Number of samples assigned to the project "
                f"{self.project_id}: {len(samples)}"
            )
        except client.APIClientError:  # pylint: disable=try-except-raise
            raise

    def _valid_prefix(self):
        """Validate if passed prefix starts with the correct sequence."""
        if not self.prefix.startswith(UPLOAD_PREFIX):
            self.echo_error(
                f"Invalid destination path. Must start with {UPLOAD_PREFIX}"
            )
            return False
        return True

    # duplicated in upload/main.py with the exception difference
    def _get_paginated_sample_sheet(self):
        """Paginate over all sample sheet pages.

        Yields:
            paginated lists of uploads
        """
        more = True
        next_link = None
        while more:
            self.echo_debug("Get sample sheet page")
            resp = self._get_sample_sheet(next_link)
            yield resp.results
            next_link = resp.meta.next
            more = next_link is not None

    @backoff.on_exception(
        backoff.expo,
        (client.APIClientTimeout),
        max_tries=5,
        max_time=30,
    )
    def _get_sample_sheet(self, next_link=None):
        """Get sample sheet page."""
        return self.api_client.get_sample_sheet(
            gncv_path=self.prefix,
            assigned_status=self.status,
            next_link=next_link,
        )

    def _assign_samples(self, samples):
        """Assign samples to the project optionally passing metadata."""
        try:
            # prepare metadata
            metadata = None
            if self.metadata_json is not None:
                metadata = json.loads(self.metadata_json)
                self.echo_info("Assigning metadata to the uploaded samples.")
            assigned_count = 0
            for samples_batch in batchify(samples, batch_size=ASSIGN_BATCH_SIZE):
                try:
                    samples_batch_len = len(samples_batch)
                    self.echo_info(f"Assigning batch: {samples_batch_len}")
                    self.api_client.add_samples_to_project(
                        samples_batch, self.project_id, metadata
                    )
                    assigned_count += samples_batch_len
                    self.echo_info(f"Total assigned: {assigned_count}")
                except client.APIClientError as err:
                    self.echo_debug(err)
                    self.echo_error("There was an error assigning/running samples.")
                    if assigned_count > 0:
                        self.echo_warning(
                            "Some of the samples were assigned. "
                            "Please use the Web UI to assign "
                            "the rest of the samples."
                        )
                    else:
                        self.echo_error("There was an error assigning samples.")
                    raise
            self.echo_info("Assigned all samples to a project.")

        except client.APIClientError as err:
            self.echo_debug(err.message)
            self.echo_error("There was an error assigning samples.")
            raise
