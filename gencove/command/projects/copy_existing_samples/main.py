"""Copy existing samples to a project subcommand."""
from typing import Generator

import backoff

from .utils import get_line
from ...base import Command
from ...utils import is_valid_uuid
from .... import client
from ....constants import IMPORT_BATCH_SIZE, SampleArchiveStatus, SampleStatus
from ....exceptions import ValidationError
from ....models import ProjectSamples, SampleDetails
from ....utils import batchify


class CopyExistingSamples(Command):
    """Copy existing samples command executor."""

    def __init__(
        self, project_id, source_project_id, source_sample_ids, credentials, options
    ):
        super().__init__(credentials, options)
        self.project_id = project_id
        self.source_project_id = source_project_id
        self.source_sample_ids = source_sample_ids

    def initialize(self):
        """Initialize copy-existing-samples subcommand."""
        self.login()

    def validate(self):
        """Validate command input.

        Raises:
            ValidationError - if something is wrong with command parameters.
        """
        if self.source_project_id and not is_valid_uuid(self.source_project_id):
            raise ValidationError("Source project ID is not valid. Exiting.")
        if (self.source_sample_ids and self.source_project_id) or (
            not self.source_sample_ids and not self.source_project_id
        ):
            raise ValidationError(
                "Either --source-project-id or --sample-ids option must be"
                " provided, but not both."
            )
        if self.project_id == self.source_project_id:
            raise ValidationError("Source and destination project must be different.")

    def execute(self):
        """Copy existing samples to the given project."""
        if self.source_project_id:
            self.echo_debug(
                "No samples given, copying all succeeded and available"
                f" samples from source project {self.source_project_id}."
            )
            self.source_sample_ids = []
            for sample in self.get_paginated_samples():
                self.source_sample_ids.append(str(sample.id))
            self.echo_debug(
                f"Samples to copy from project: {len(self.source_sample_ids)}"
            )
        self.echo_info(f"Copy existing samples to the project: {self.project_id}")
        try:
            # Copy existing samples to the project.
            for samples_batch in batchify(
                self.source_sample_ids, batch_size=IMPORT_BATCH_SIZE
            ):
                copy_existing_samples_response = self.api_client.copy_existing_samples(
                    self.project_id, samples_batch
                )
                for copied_sample in copy_existing_samples_response.samples:
                    self.echo_data(get_line(copied_sample))
            self.echo_info(
                f"Number of samples copied into the project {self.project_id}: "
                f"{len(self.source_sample_ids)}"
            )
        except client.APIClientError as err:
            self.echo_debug(err.message)
            self.echo_error("There was an error copying samples.")
            raise

    def get_paginated_samples(
        self,
    ) -> Generator[SampleDetails, None, None]:
        """Paginate over all completed samples for the destination.

        Yields:
            Samples in succeeded or failed_qc state that have files.
        """
        more = True
        next_link = None
        while more:
            self.echo_debug("Get all completed samples")
            resp = self.get_samples(next_link)
            if resp.results:
                for sample in resp.results:
                    if sample.last_status.status in ["failed qc", "succeeded"]:
                        yield sample
            next_link = resp.meta.next
            more = next_link is not None

    @backoff.on_exception(
        backoff.expo,
        (client.APIClientTimeout),
        max_tries=2,
        max_time=30,
    )
    def get_samples(self, next_link=None) -> ProjectSamples:
        """Get all completed samples page."""
        return self.api_client.get_project_samples(
            project_id=self.source_project_id,
            next_link=next_link,
            sample_status=SampleStatus.COMPLETED.value,
            sample_archive_status=SampleArchiveStatus.AVAILABLE.value,
        )
