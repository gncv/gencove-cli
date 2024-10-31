"""Configure explorer data restore definition."""
from concurrent.futures import ThreadPoolExecutor

from ..common import (
    GencoveExplorerManager,
    request_is_from_explorer,
    validate_explorer_user_data,
)
from ....base import Command
from ....utils import user_has_aws_in_path
from .....constants import RESTORE_TIERS_SUPPORTED
from .....exceptions import ValidationError


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

        # populated after self.execute() is called
        self.organization_users = None

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
        if self.tier not in RESTORE_TIERS_SUPPORTED:
            raise ValidationError(
                f"Tier can only be one of: {RESTORE_TIERS_SUPPORTED}."
            )

    def initialize(self):
        """Initialize restore subcommand."""
        self.login()
        self.user = self.api_client.get_user_details()
        self.organization = self.api_client.get_organization_details()

        if not request_is_from_explorer():
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
            organization_users=self.api_client.get_organization_users(),
        )

        bucket, _ = (
            explorer_manager.translate_path_to_s3_path(self.path)
            .lstrip("s3://")
            .split("/", 1)
        )
        s3_client = explorer_manager.thread_safe_client("s3")

        def restore_archived(obj) -> bool:
            """Restores archived file by calling S3 API.

            Args:
                obj (dict): Contains the "Key" of the object to
                    be restored.

            Returns:
                bool: False if the object is not archived,
                    otherwise returns True.
            """
            self.echo_debug(f"restore_archived: {obj}")

            if obj.get("StorageClass") not in [
                "GLACIER",
                "DEEP_ARCHIVE",
            ]:
                return False  # skip non-archived files

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

            return True

        paginated_response = explorer_manager.list_s3_objects(self.path)
        obj_counts = {"skipped": 0, "restored": 0}
        with ThreadPoolExecutor() as executor:
            for response in paginated_response:
                for restored in executor.map(restore_archived, response["Contents"]):
                    if restored:
                        obj_counts["restored"] += 1
                    else:
                        obj_counts["skipped"] += 1

        if obj_counts["restored"]:
            self.echo_info(
                f"Restoring {obj_counts['restored']} objects in {self.path}."
                f" They will be available for {self.days} days."
            )

        if obj_counts["skipped"]:
            self.echo_info(
                f"Skipped {obj_counts['skipped']} objects that are not archived."
            )
