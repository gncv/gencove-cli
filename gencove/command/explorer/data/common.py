"""Common code shared across data commands is stored here"""
import sys
import uuid
from dataclasses import dataclass
from typing import List, Optional, Tuple, Literal

# pylint: disable=wrong-import-order
from gencove.exceptions import ValidationError
from gencove.models import AWSCredentials, OrganizationDetails, UserDetails

import sh


@dataclass
class GencoveExplorerManager:  # pylint: disable=too-many-instance-attributes,too-many-public-methods # noqa: E501
    """Port of Explorer GencoveClient and related functionality"""

    aws_session_credentials: AWSCredentials

    user_id: str
    organization_id: str

    # Constants ported from Gencove Explorer package
    # https://gitlab.com/gencove/platform/explorer-sdk/-/blob/main/gencove_explorer/constants.py  # noqa: E501 # pylint:
    # disable=line-too-long
    # pylint: disable=invalid-name
    USERS: str = "users"
    ORG: str = "org"
    GENCOVE: str = "gencove"
    ME: str = "me"
    S3_PROTOCOL: str = "s3://"
    EXPLORER_SCHEME: str = "e://"
    DATA_BUCKET: str = "gencove-explorer-data"
    USER_DIR: str = "files"
    DATA_DIR: str = USER_DIR
    SHARED_DIR: str = "shared"
    SCRATCH_DIR: str = "scratch"
    USERS_DIR: str = "users"
    TMP_DIR: str = f"{DATA_DIR}/tmp"  # nosec: B108

    # pylint: enable=invalid-name

    def __post_init__(self):
        # pylint: disable=invalid-name
        self.NAMESPACES: dict = {
            self.USERS: self.data_s3_prefix,
            self.ORG: self.data_org_s3_prefix,
            self.GENCOVE: self.data_gencove_s3_prefix,
        }
        self.NAMESPACE_KEYS: Tuple = tuple(self.NAMESPACES.keys())
        # pylint: enable=invalid-name

    @property
    def bucket_name(self) -> str:
        """Construct bucket name based on short form of org ID"""
        organization_id_short = self.organization_id.replace("-", "")[:12]
        return f"gencove-explorer-{organization_id_short}"

    @property
    def aws_env(self) -> dict:
        """Dict containing AWS credentials"""
        return {
            "AWS_ACCESS_KEY_ID": self.aws_session_credentials.access_key,
            "AWS_SECRET_ACCESS_KEY": self.aws_session_credentials.secret_key,
            "AWS_SESSION_TOKEN": self.aws_session_credentials.token,
        }

    @property
    def users_prefix(self) -> str:
        """S3 prefix for all users"""
        return f"{self.USERS_DIR}"

    @property
    def base_prefix(self) -> str:
        """Base S3 prefix for all objects to be uploaded/retrieved for user.

        e.g. user/1111/
        """
        return f"{self.users_prefix}/{self.user_id}"

    @property
    def shared_prefix(self) -> str:
        """Base S3 prefix for all objects to be uploaded/retrieved for organization."""
        return self.SHARED_DIR

    @property
    def data_org_prefix(self) -> str:
        """Base S3 prefix for all data to be uploaded/retreived for organization."""
        return f"{self.SHARED_DIR}/{self.DATA_DIR}"

    @property
    def data_prefix(self) -> str:
        """Base S3 prefix for all data to be uploaded/retreived for user."""
        return f"{self.base_prefix}/{self.DATA_DIR}"

    @property
    def user_prefix(self) -> str:
        """Base S3 prefix for user dir"""
        return f"{self.base_prefix}/{self.USER_DIR}"

    @property
    def tmp_prefix(self) -> str:
        """Base S3 prefix for temp user dir"""
        return f"{self.base_prefix}/{self.TMP_DIR}"

    @property
    def tmp_org_prefix(self) -> str:
        """S3 prefix for temp shared dir"""
        return f"{self.shared_prefix}/{self.TMP_DIR}"

    @property
    def scratch_prefix(self) -> str:
        """Base S3 prefix for scratch dir"""
        return f"{self.base_prefix}/{self.SCRATCH_DIR}"

    @property
    def user_scratch_s3_prefix(self) -> str:
        """S3 prefix for user scratch dir"""
        return f"{self.S3_PROTOCOL}{self.bucket_name}/{self.scratch_prefix}"

    @property
    def shared_org_s3_prefix(self) -> str:
        """S3 prefix for org dir"""
        return f"{self.S3_PROTOCOL}{self.bucket_name}/{self.shared_prefix}"

    @property
    def data_gencove_s3_prefix(self) -> str:
        """S3 prefix for gencove data dir"""
        return f"{self.S3_PROTOCOL}{self.DATA_BUCKET}/{self.DATA_DIR}"

    @property
    def data_org_s3_prefix(self) -> str:
        """S3 prefix for org data dir"""
        return f"{self.S3_PROTOCOL}{self.bucket_name}/{self.data_org_prefix}"

    @property
    def data_s3_prefix(self) -> str:
        """S3 prefix for user data dir"""
        return f"{self.S3_PROTOCOL}{self.bucket_name}/{self.data_prefix}"

    @property
    def users_s3_prefix(self) -> str:
        """Prefix for users dir"""
        return f"{self.S3_PROTOCOL}{self.bucket_name}/{self.users_prefix}"

    def uri_ok(self, path: Optional[str]) -> bool:
        """Tests if supplied path is valid

        Args:
            path (Optional[str]): Path to test

        Returns:
            True if path valid, False otherwise
        """
        return path is not None and path.startswith(self.EXPLORER_SCHEME)

    def translate_path_to_s3_path(self, path: Optional[str]) -> Optional[str]:
        """Accepts any input path and converts `e://` path to `s3://` path if
        input is an `e://` path

        Supported paths:
        e://gencove/...
        e://org/...
        e://users/<user-id>/...
        e://users/me/...
        """
        if path is None:
            return None
        if path.startswith(self.EXPLORER_SCHEME):
            path_noprefix_split = path.removeprefix(self.EXPLORER_SCHEME).split("/")
            namespace = path_noprefix_split[0]
            if namespace not in self.NAMESPACES:
                raise ValueError(
                    f"Invalid namespace '{namespace}'. Valid namespaces are: "
                    f"{', '.join(self.NAMESPACE_KEYS)}"
                )
            prefix_s3 = self.NAMESPACES[namespace]
            path_remainder = "/".join(path_noprefix_split[1:])
            if namespace == self.USERS:
                if len(path_noprefix_split) <= 1:
                    raise ValueError(f"A user id (or '{self.ME}') must be specified")
                user_id = path_noprefix_split[1]
                if user_id != self.ME:
                    try:
                        uuid.UUID(user_id)
                    except ValueError:
                        raise ValueError(  # pylint: disable=raise-missing-from
                            f"User id '{user_id}' is not a valid UUID (or '{self.ME}')"
                        )
                    prefix_s3 = self.users_s3_prefix + f"/{user_id}"
                path_remainder = "/".join(path_noprefix_split[2:])
            path = f"{prefix_s3}/{path_remainder}"
        return path

    def list_users(self):
        """List e:// user dir"""
        sh.aws.s3.ls(  # pylint: disable=no-member
            f"{self.S3_PROTOCOL}{self.bucket_name}/{self.USERS_DIR}/",
            _in=sys.stdin,
            _out=sys.stdout,
            _err=sys.stderr,
            _env=self.aws_env,
        )

    def execute_aws_s3_path(
        self,
        cmd: Literal["ls", "rm"],
        path: str,
        args: List[str],
    ) -> List[str]:
        """Executes the respective `aws s3` single-path commands with `e://` paths
        translated to `s3://` paths

        Args:
            cmd (Literal["ls", "rm"]): AWS S3 command to execute
            path (str): Path to execute command against
            args (List[str]): List of additional args to forward to AWS CLI

        Returns:
            List of args passed to AWS CLI
        """
        if not self.uri_ok(path):
            raise ValueError(f"Path {path} does not start with {self.EXPLORER_SCHEME}")
        s3_command = [
            cmd,
            self.translate_path_to_s3_path(path),
            *args,
        ]
        sh.aws.s3(  # pylint: disable=no-member
            s3_command,
            _in=sys.stdin,
            _out=sys.stdout,
            _err=sys.stderr,
            _env=self.aws_env,
        )
        return s3_command

    def execute_aws_s3_src_dst(
        self, cmd: Literal["cp", "sync"], source: str, destination: str, args: List[str]
    ) -> List[str]:
        """Executes the respective `aws s3` dual-path (source-to-destination)
        commands with e://` paths translated to `s3://` paths

        Args:
            cmd (Literal["cp", "sync"]): AWS S3 command to execute
            source: Source path for S3 command
            destination: Destination path for S3 command
            args: List of additional args to forward to AWS CLI

        Returns:
            List of args passed to AWS CLI
        """
        if not self.uri_ok(source) and not self.uri_ok(destination):
            raise ValueError(
                f"At least one of source or destination must start with "
                f"{self.EXPLORER_SCHEME}"
            )
        s3_command = [
            cmd,
            self.translate_path_to_s3_path(source),
            self.translate_path_to_s3_path(destination),
            *args,
        ]
        sh.aws.s3(  # pylint: disable=no-member
            s3_command,
            _in=sys.stdin,
            _out=sys.stdout,
            _err=sys.stderr,
            _env=self.aws_env,
        )
        return s3_command


def validate_explorer_user_data(user: UserDetails, organization: OrganizationDetails):
    """Validate user and organization data"""
    if not user.explorer_enabled:
        raise ValidationError(
            "Explorer is not enabled on your user account, quitting. "
            "Please reach out to your organization owner to inquire "
            "about Gencove Explorer."
        )

    if not user or not organization:
        raise ValidationError("Could not retrieve user details, quitting.")
