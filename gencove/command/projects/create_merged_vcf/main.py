"""Merge project's VCF files executor."""
from ..status_merged_vcf.utils import get_line
from ...base import Command
from ...utils import is_valid_uuid
from .... import client
from ....exceptions import ValidationError


class CreateMergedVCF(Command):
    """Merge project's VCF files executor."""

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

    # no retry for timeouts in order to avoid duplicate heavy operations on
    # the backend
    def execute(self):
        """Make a request to merge VCF files for a given project."""
        self.echo_debug(
            "Merging VCF files for project {}".format(self.project_id)
        )
        try:
            created_merge_details = self.api_client.create_merged_vcf(
                self.project_id
            )
            self.echo_debug(created_merge_details)
            self.echo_info(
                "Issued merge request for project {}".format(self.project_id),
            )
            self.echo_data(get_line(created_merge_details))
        except client.APIClientError as err:
            self.echo_debug(err)
            if err.status_code == 400:
                self.echo_error("There was an error creating merged VCF.")
            elif err.status_code == 404:
                self.echo_error(
                    "Project {} does not exist or you do not have "
                    "permission required to access it.".format(
                        self.project_id
                    )
                )
            raise
