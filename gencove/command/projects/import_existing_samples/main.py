"""Import existing samples to a project subcommand."""
import json

from .utils import get_line
from ...base import Command
from ...utils import is_valid_json, is_valid_uuid
from .... import client
from ....exceptions import ValidationError


class ImportExistingSamples(Command):
    """Import existing samples command executor."""

    def __init__(self, project_id, sample_ids, credentials, options):
        super().__init__(credentials, options)
        self.project_id = project_id
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
        if is_valid_uuid(self.project_id) is False:
            raise ValidationError("Project ID is not valid. Exiting.")
        if not all(is_valid_uuid(s_id) for s_id in self.sample_ids):
            raise ValidationError("Not all sample IDs are valid. Exiting.")
        if self.metadata_json and is_valid_json(self.metadata_json) is False:
            raise ValidationError("Metadata JSON is not valid. Exiting.")

    def execute(self):
        """Import existing samples to the given project."""
        metadata = None
        if self.metadata_json is not None:
            metadata = json.loads(self.metadata_json)
            self.echo_info("Assigning metadata to the importing samples.")
        self.echo_info(f"Import existing samples to the project: {self.project_id}")
        try:
            # Import existing samples to the project optionally
            # passing metadata.
            import_existing_samples_response = self.api_client.import_existing_samples(
                self.project_id, self.sample_ids, metadata
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
