"""Merge project's VCF files executor."""
import backoff

from .utils import get_line
from ...base import Command
from ...utils import is_valid_uuid
from .... import client
from ....exceptions import ValidationError


class StatusMergedVCF(Command):
    """Executor for retrieving the status of a job for merging project's VCF
    files.
    """

    def __init__(
        self,
        project_id,
        credentials,
        options,
    ):
        super().__init__(credentials, options)
        self.project_id = project_id

    def initialize(self):
        """Initialize subcommand."""
        self.login()

    def validate(self):
        """Validate command input.

        Raises:
            ValidationError - if something is wrong with command parameters.
        """
        if is_valid_uuid(self.project_id) is False:
            raise ValidationError("Project ID is not valid. Exiting.")

    @backoff.on_exception(
        backoff.expo,
        (client.APIClientTimeout),
        max_tries=5,
        max_time=30,
    )
    def execute(self):
        """Get a status of a request to merge VCF files for a given project."""
        self.echo_debug(
            "Retrieving the status of a merge VCF files operation for "
            "project {}".format(self.project_id)
        )
        try:
            merge_details_status = self.api_client.retrieve_merged_vcf(
                self.project_id
            )
            self.echo_debug(merge_details_status)
            if merge_details_status["last_status"]["status"] == "failed":
                self.echo_warning("The job failed merging.")
            self.echo_data(get_line(merge_details_status))
        except client.APIClientError as err:
            self.echo_debug(err)
            if err.status_code == 400:
                self.echo_error(
                    "There was an error checking the status of "
                    "a merged VCF."
                )
            elif err.status_code == 404:
                self.echo_error(
                    "Project {} does not exist or you do not have "
                    "permission required to access it or there are no "
                    "running jobs associated with it.".format(self.project_id)
                )
            raise
