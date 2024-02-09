"""Get Reference Genome command executor."""
import re

import backoff

from gencove import client  # noqa: I100
from gencove.command.base import Command
from gencove.command.download.utils import (
    _create_filepath,
    download_file,
    get_filename_from_download_url,
)
from gencove.command.utils import validate_file_types
from gencove.constants import FileTypesObject
from gencove.exceptions import ValidationError


class GetReferenceGenome(Command):
    """Get Reference Genome command executor."""

    def __init__(
        self, project_id, destination, file_types, credentials, options, no_progress
    ):
        super().__init__(credentials, options)
        self.project_id = project_id
        self.destination = destination
        self.file_types = file_types
        self.no_progress = no_progress

    def initialize(self):
        """Initialize subcommand."""
        self.login()

    def validate(self):
        """Validate command input."""
        try:
            valid_file_types = self.api_client.get_file_types(
                project_id=self.project_id,
                object_param=FileTypesObject.REFERENCE_GENOME.value,
            ).results
            invalid_file_types = validate_file_types(self.file_types, valid_file_types)
            if invalid_file_types:
                raise ValidationError(
                    f"Invalid file types: {', '.join(invalid_file_types)}. "
                    "Run 'gencove file-types --object reference-genome' command for a "
                    "list of valid file types. "
                    "Use with --project-id option to see project file types."
                )
        except client.APIClientError as err:
            self.echo_debug(err)
            self.echo_warning("There was an error while validating file types.")

    @backoff.on_exception(
        backoff.expo,
        (client.APIClientTimeout),
        max_tries=5,
        max_time=30,
    )
    @backoff.on_exception(
        backoff.expo,
        client.APIClientTooManyRequestsError,
        max_tries=20,
    )
    def execute(self):
        """Download Reference Genome files for a given project."""
        self.echo_debug(
            f"Downloading Reference Genome files for project {self.project_id}"
        )
        try:
            project = self.api_client.get_project(self.project_id)
            self.echo_debug(project)
            file_types_re = re.compile("|".join(self.file_types), re.IGNORECASE)
            for file in project.files:
                if self.file_types and not file_types_re.match(file.file_type):
                    self.echo_debug(
                        "Deliverable file type is not in desired file types"
                    )
                    continue
                self.echo_debug(f"Downloading {file.file_type}, id {file.id}")
                filename = get_filename_from_download_url(file.download_url)
                file_path = _create_filepath(self.destination, "", filename)
                self.echo_debug(f"file path is: {file_path}")
                download_file(
                    file_path,
                    file.download_url,
                    no_progress=self.no_progress,
                )
        except client.APIClientError as err:
            self.echo_debug(err)
            if err.status_code == 404:
                self.echo_error(f"Project {self.project_id} does not exist.")
            raise
