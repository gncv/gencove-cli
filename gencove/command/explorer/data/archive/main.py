"""Configure explorer data archive definition."""
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

import botocore
import botocore.exceptions

from ..common import (
    GencoveExplorerManager,
    request_is_from_explorer_instance,
    validate_explorer_user_data,
)
from ....base import Command
from ....utils import user_has_aws_in_path
from .....models import ExplorerDataCredentials


class Archive(Command):
    """Archive Explorer contents command executor."""

    def __init__(self, ctx, path, credentials, options):
        super().__init__(credentials, options)
        self.ctx = ctx
        self.path = path

        # Populated after self.login() is called
        self.user = None
        self.organization = None
        self.aws_session_credentials: Optional[ExplorerDataCredentials] = None

    def validate(self):
        """Validate archive"""
        validate_explorer_user_data(self.user, self.organization)
        user_has_aws_in_path(raise_exception=True)

    def initialize(self):
        """Initialize archive subcommand."""
        self.login()
        self.user = self.api_client.get_user_details()
        self.organization = self.api_client.get_organization_details()

        if not request_is_from_explorer_instance():
            self.aws_session_credentials = (
                self.api_client.get_explorer_data_credentials()
            )

    def execute(self):
        """Make a request to archive Explorer objects."""
        self.echo_debug("Archive Explorer contents.")

        explorer_manager = GencoveExplorerManager(
            aws_session_credentials=self.aws_session_credentials,
            user_id=str(self.user.id),
            organization_id=str(self.organization.id),
        )

        bucket, _ = (
            explorer_manager.translate_path_to_s3_path(self.path)
            .lstrip("s3://")
            .split("/", 1)
        )
        s3_client = explorer_manager.thread_safe_client("s3")

        def set_archive_tag(obj):
            if obj.get("StorageClass") != "STANDARD":
                return  # skip already archived files

            try:
                s3_client.put_object_tagging(
                    Bucket=bucket,
                    Key=obj["Key"],
                    Tagging={
                        "TagSet": [
                            {
                                "Key": "Archive",
                                "Value": "DEEP_ARCHIVE",
                            }
                        ]
                    },
                )
            except botocore.exceptions.ClientError as ex:
                if (
                    ex.response
                    and ex.response.get("Error", {}).get("Code") == "AccessDenied"
                ):
                    # Check if object is already set to be archived
                    response = s3_client.get_object_tagging(
                        Bucket=bucket,
                        Key=obj["Key"],
                    )
                    archive_tag = None
                    for tag_set in response.get("TagSet", []):
                        if tag_set["Key"] == "Archive":
                            archive_tag = tag_set["Value"]
                    if archive_tag:
                        return  # skip if file is already set to be archived
                raise

            self.echo_data(f"archive: {obj['Key']}")

        paginated_response = explorer_manager.list_objects(self.path)
        obj_count = 0
        with ThreadPoolExecutor() as executor:
            for response in paginated_response:
                for _ in executor.map(set_archive_tag, response["Contents"]):
                    obj_count += 1

        self.echo_info(f"Archived {obj_count} objects in {self.path}")
