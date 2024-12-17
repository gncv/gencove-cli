"""Configure explorer data archive definition."""
import os
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

import botocore
import botocore.exceptions

from ..common import (
    GencoveExplorerManager,
    request_is_from_explorer,
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
        self.user_id = None
        self.organization_id = None
        self.explorer_enabled = False
        self.aws_session_credentials: Optional[ExplorerDataCredentials] = None

        # populated after self.execute() is called
        self.organization_users = None

    def validate(self):
        """Validate archive"""
        validate_explorer_user_data(
            self.user_id, self.organization_id, self.explorer_enabled
        )
        user_has_aws_in_path(raise_exception=True)

    def initialize(self):
        """Initialize archive subcommand."""
        self.login()

        if not request_is_from_explorer():
            user_data = self.api_client.get_user_details()
            self.user_id = user_data.id
            self.organization_id = self.api_client.get_organization_details().id
            self.explorer_enabled = user_data.explorer_enabled
            self.aws_session_credentials = (
                self.api_client.get_explorer_data_credentials()
            )
        else:
            self.user_id = uuid.UUID(os.getenv("GENCOVE_USER_ID"))
            self.organization_id = uuid.UUID(os.getenv("GENCOVE_ORGANIZATION_ID"))
            self.explorer_enabled = True

    def execute(self):
        """Make a request to archive Explorer objects."""
        self.echo_debug("Archive Explorer contents.")

        explorer_manager = GencoveExplorerManager(
            aws_session_credentials=self.aws_session_credentials,
            user_id=str(self.user_id),
            organization_id=str(self.organization_id),
            organization_users=self.api_client.get_organization_users(),
        )

        bucket, _ = (
            explorer_manager.translate_path_to_s3_path(self.path)
            .lstrip("s3://")
            .split("/", 1)
        )
        s3_client = explorer_manager.thread_safe_client("s3")

        def set_archive_tag(obj):
            """Set Archive tag to object that will be later archived
            by lifecycle rule.

            Args:
                obj (dict): Contains Key of the object to be archived.

            Returns:
                bool: False if already archived, True otherwise.
            """
            self.echo_debug(f"set_archive_tag: {obj}")

            if obj.get("StorageClass") != "STANDARD":
                return False  # skip already archived files

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
                        return False  # skip if file is already set to be archived
                raise

            self.echo_data(f"archive: {obj['Key']}")

            return True

        paginated_response = explorer_manager.list_s3_objects(self.path)
        obj_counts = {"archived": 0, "skipped": 0}
        with ThreadPoolExecutor() as executor:
            for response in paginated_response:
                for archived in executor.map(set_archive_tag, response["Contents"]):
                    if archived:
                        obj_counts["archived"] += 1
                    else:
                        obj_counts["skipped"] += 1

        if obj_counts["archived"]:
            self.echo_info(f"Archived {obj_counts['archived']} objects in {self.path}.")

        if obj_counts["skipped"]:
            self.echo_info(
                f"Skipped {obj_counts['skipped']} objects that were previously "
                "archived."
            )
