"""Configure explorer data archive definition."""
import sys
from typing import Optional
from concurrent.futures import ThreadPoolExecutor

import boto3

from gencove.models import ExplorerDataCredentials
from ..common import (
    GencoveExplorerManager,
    request_is_from_explorer_instance,
    validate_explorer_user_data,
)
from ....base import Command
from ....utils import user_has_aws_in_path


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

        if self.aws_session_credentials:
            boto_session = boto3.Session(
                aws_access_key_id=self.aws_session_credentials.access_key,
                aws_secret_access_key=self.aws_session_credentials.secret_key,
                aws_session_token=self.aws_session_credentials.token,
                region_name=self.aws_session_credentials.region_name,
            )
        else:
            boto_session = boto3.Session()

        s3_client = boto_session.client("s3")

        s3_path = explorer_manager.translate_path_to_s3_path(self.path)

        bucket, prefix = s3_path.lstrip("s3://").split("/", 1)

        paginated_response = s3_client.get_paginator("list_objects_v2").paginate(
            Bucket=bucket,
            Prefix=prefix,
            PaginationConfig={
                "PageSize": 1_000,
            },
        )

        def set_archive_tag(obj):
            if obj.get("StorageClass") != "STANDARD":
                return  # skip already archived files

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
            print("archive:", obj["Key"])

        obj_count = 0
        with ThreadPoolExecutor() as executor:
            for response in paginated_response:
                for _ in executor.map(set_archive_tag, response["Contents"]):
                    obj_count += 1

        print(f"Archived {obj_count} objects in {self.path}")
