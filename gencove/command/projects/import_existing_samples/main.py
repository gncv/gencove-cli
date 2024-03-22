"""Import existing samples to a project subcommand."""
import json
from typing import Generator, Optional, List

import backoff

from .utils import get_line
from ...base import Command
from ...utils import is_valid_json
from .... import client
from ....constants import IMPORT_BATCH_SIZE, SampleStatus, SampleArchiveStatus
from ....exceptions import ValidationError
from ....models import ProjectSamples, SampleDetails
from ....utils import batchify


class ImportExistingSamples(Command):
    """Import existing samples command executor."""

    def __init__(self, project_id, source_project_id, sample_ids, credentials, options):
        super().__init__(credentials, options)
        self.project_id = project_id
        self.source_project_id = source_project_id
        self.sample_ids = sample_ids
        self.metadata_json = options.metadata_json

    def initialize(self):
        """Initialize import-existing-samples subcommand."""
        self.login()

    def validate(self):
        """Validate command input.

        Raises:
            ValidationError - if something is wrong with command parameters.
        """
        if self.metadata_json and is_valid_json(self.metadata_json) is False:
            raise ValidationError("Metadata JSON is not valid. Exiting.")
        if (self.sample_ids and self.source_project_id) or (
            not self.sample_ids and not self.source_project_id
        ):
            raise ValidationError(
                "Either --source-project-id or --sample-ids option must be"
                " provided, but not both."
            )
        if self.project_id == self.source_project_id:
            raise ValidationError("Source and destination project must be different.")

    def execute(self):
        """Import existing samples to the given project."""
        if self.source_project_id:
            self.echo_debug(
                "No samples given, importing all succeeded and available"
                f" samples from source project {self.source_project_id}."
            )
            self.sample_ids = []
            for samples in self.get_paginated_samples():
                if not samples:
                    continue
                for sample in samples:
                    self.sample_ids.append(str(sample.id))
            self.echo_debug(f"Samples to import from project: {len(self.sample_ids)}")
        metadata = None
        if self.metadata_json is not None:
            metadata = json.loads(self.metadata_json)
            self.echo_info("Assigning metadata to the importing samples.")
        self.echo_info(f"Import existing samples to the project: {self.project_id}")
        try:
            # Import existing samples to the project optionally
            # passing metadata.
            for samples_batch in batchify(
                self.sample_ids, batch_size=IMPORT_BATCH_SIZE
            ):
                import_existing_samples_response = (
                    self.api_client.import_existing_samples(
                        self.project_id, samples_batch, metadata
                    )
                )
                for imported_sample in import_existing_samples_response.samples:
                    self.echo_data(get_line(imported_sample))
            self.echo_info(
                f"Number of samples imported into the project {self.project_id}: "
                f"{len(self.sample_ids)}"
            )
            if metadata:
                self.echo_info("Metadata attached to each sample.")
        except client.APIClientError as err:
            self.echo_debug(err.message)
            self.echo_error("There was an error importing samples.")
            raise

    def get_paginated_samples(
        self,
    ) -> Generator[Optional[List[SampleDetails]], None, None]:
        """Paginate over all sample sheets for the destination.

        Yields:
            paginated lists of samples
        """
        more = True
        next_link = None
        while more:
            self.echo_debug("Get sample sheet page")
            resp = self.get_samples(next_link)
            yield resp.results
            next_link = resp.meta.next
            more = next_link is not None

    @backoff.on_exception(
        backoff.expo,
        (client.APIClientTimeout),
        max_tries=2,
        max_time=30,
    )
    def get_samples(self, next_link=None) -> ProjectSamples:
        """Get sample sheet page."""
        return self.api_client.get_project_samples(
            project_id=self.source_project_id,
            next_link=next_link,
            sample_status=SampleStatus.SUCCEEDED.value,
            sample_archive_status=SampleArchiveStatus.AVAILABLE.value,
        )
