"""Import existing samples to a project subcommand."""
import json

from .utils import get_line, is_valid_client_id
from ...base import Command
from ...utils import is_valid_json, is_valid_uuid
from .... import client
from ....exceptions import ValidationError


class ImportExistingSamples(Command):
    """Import existing samples command executor."""

    def __init__(self, project_id, samples, credentials, options):
        super().__init__(credentials, options)
        self.project_id = project_id
        self.samples = samples
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
        if is_valid_json(self.samples) is False:
            raise ValidationError("Samples JSON is not valid. Exiting.")
        # set immediatelly
        self.samples = json.loads(self.samples)
        if self.is_valid_samples_contents() is False:
            raise ValidationError(
                "The samples JSON must be a JSON array of objects where "
                "each has sample_id and an optional client_id keys. Exiting."
            )
        for sample in self.samples:
            if is_valid_uuid(sample["sample_id"]) is False:
                raise ValidationError(
                    f"Sample ID {sample['sample_id']} is not a valid UUID. Exiting."
                )
            if is_valid_client_id(sample.get("client_id", "")) is False:
                raise ValidationError(
                    f"Client ID: {sample['client_id']} for the "
                    f"sample {sample['sample_id']} is not valid. "
                    "It cannot contain an underscore. Exiting."
                )
        if self.metadata_json and is_valid_json(self.metadata_json) is False:
            raise ValidationError("Metadata JSON is not valid. Exiting.")

    def execute(self):
        """Import existing samples to the given project."""
        clean_samples = self.clean_samples()
        metadata = None
        if self.metadata_json is not None:
            metadata = json.loads(self.metadata_json)
            self.echo_info("Assigning metadata to the importing samples.")
        self.echo_info(f"Import existing samples to the project: {self.project_id}")
        try:
            # Import existing samples to the project optionally
            # passing metadata.
            import_existing_samples_response = self.api_client.import_existing_samples(
                self.project_id, clean_samples, metadata
            )
            for imported_sample in import_existing_samples_response.samples:
                self.echo_data(get_line(imported_sample))
            self.echo_info(
                f"Number of samples imported into the project {self.project_id}: "
                f"{len(clean_samples)}"
            )
            if metadata:
                self.echo_info("Metadata attached to each sample.")
        except client.APIClientError as err:
            self.echo_debug(err.message)
            self.echo_error("There was an error importing samples.")
            raise

    def is_valid_samples_contents(self):
        """Test if samples member is of a legal format.

        Returns:
            bool: True if samples are valid, False if not
        """
        if not isinstance(self.samples, list):
            return False
        for sample in self.samples:
            if not isinstance(sample, dict):
                return False
            if "sample_id" not in sample:
                return False
        return True

    def clean_samples(self):
        """Sanitize samples member so it sends only the required values.

        Returns:
            list: items are dictionaries with sample_id key and an
                optional client_id key
        """
        clean_samples = []
        for sample in self.samples:
            clean_sample = {"sample_id": sample["sample_id"]}
            if "client_id" in sample:
                clean_sample["client_id"] = sample["client_id"]
            clean_samples.append(clean_sample)
        return clean_samples
