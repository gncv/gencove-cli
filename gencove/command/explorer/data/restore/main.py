"""Configure explorer data restore definition."""
from concurrent.futures import ThreadPoolExecutor

from ..common import (
    GencoveExplorerManager,
    request_is_from_explorer_instance,
    validate_explorer_user_data,
)
from ....base import Command
from ....utils import user_has_aws_in_path
from gencove.exceptions import ValidationError


class Restore(Command):
    """Restore archived Explorer contents command executor."""

    def __init__(self, ctx, path, days, tier, credentials, options):
        super().__init__(credentials, options)
        self.ctx = ctx
        self.path = path
        self.days = days
        self.tier = tier

        # Populated after self.login() is called
        self.user = None
        self.organization = None
        self.aws_session_credentials = None

    def validate(self):
        """Validate restore"""
        self.validate_tier()
        validate_explorer_user_data(self.user, self.organization)
        user_has_aws_in_path(raise_exception=True)

    def validate_tier(self):
        """Validate that tier is supported.

        Raises:
            ValidationError: If tier is not supported.
        """
        if self.tier not in ["Standard", "Expedited", "Bulk"]:
            raise ValidationError("Tier can only be one of: Standard, Expedited, Bulk.")

    def initialize(self):
        """Initialize restore subcommand."""
        self.login()
        self.user = self.api_client.get_user_details()
        self.organization = self.api_client.get_organization_details()

        if not request_is_from_explorer_instance():
            self.aws_session_credentials = (
                self.api_client.get_explorer_data_credentials()
            )

    def execute(self):
        """Make a request to restore Explorer objects."""
        self.echo_debug("List Explorer contents.")

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

        def restore_archived(obj):
            if obj.get("StorageClass") not in [
                "GLACIER",
                "DEEP_ARCHIVE",
            ]:
                return  # skip non-archived files

            # If already restored it extends the availability window
            s3_client.restore_object(
                Bucket=bucket,
                Key=obj["Key"],
                RestoreRequest={
                    "Days": self.days,
                    "GlacierJobParameters": {
                        "Tier": self.tier,
                    },
                },
            )

            self.echo_data(f"restore: {obj['Key']}")

        paginated_response = explorer_manager.list_objects(self.path)
        obj_count = 0
        with ThreadPoolExecutor() as executor:
            for response in paginated_response:
                for _ in executor.map(restore_archived, response["Contents"]):
                    obj_count += 1

        self.echo_info(f"Restored {obj_count} objects in {self.path}")
