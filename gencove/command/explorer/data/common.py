import sys
import uuid
from dataclasses import dataclass
from typing import Optional, List, Tuple

import sh


@dataclass
class GencoveExplorerManager:
    """Port of Explorer GencoveClient and related functionality"""

    aws_session_credentials: dict

    user_id: str
    organization_id: str

    # Constants ported from Gencove Explorer package
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
    # Temporary directory visible to user in EOS
    TMP_DIR: str = f"{DATA_DIR}/tmp"  # nosec: B108

    def __post_init__(self):
        self.NAMESPACES: dict = {
            self.USERS: self.data_s3_prefix,
            self.ORG: self.data_org_s3_prefix,
            self.GENCOVE: self.data_gencove_s3_prefix,
        }
        self.NAMESPACE_KEYS: Tuple = tuple(self.NAMESPACES.keys())

    @property
    def bucket_name(self) -> str:
        """Construct bucket name based on short form of org ID"""
        organization_id_short = self.organization_id.replace("-", "")[:12]
        return f"gencove-explorer-{organization_id_short}"

    @property
    def aws_env(self):
        return {
            "AWS_ACCESS_KEY_ID": self.aws_session_credentials["access_key"],
            "AWS_SECRET_ACCESS_KEY": self.aws_session_credentials["secret_key"],
            "AWS_SESSION_TOKEN": self.aws_session_credentials["token"],
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
        return f"{self.base_prefix}/{self.USER_DIR}"

    @property
    def tmp_prefix(self) -> str:
        return f"{self.base_prefix}/{self.TMP_DIR}"

    @property
    def tmp_org_prefix(self) -> str:
        return f"{self.shared_prefix}/{self.TMP_DIR}"

    @property
    def scratch_prefix(self) -> str:
        return f"{self.base_prefix}/{self.SCRATCH_DIR}"

    @property
    def user_scratch_s3_prefix(self) -> str:
        return f"{self.S3_PROTOCOL}{self.bucket_name}/{self.scratch_prefix}"

    @property
    def shared_org_s3_prefix(self) -> str:
        return f"{self.S3_PROTOCOL}{self.bucket_name}/{self.shared_prefix}"

    @property
    def data_gencove_s3_prefix(self) -> str:
        return f"{self.S3_PROTOCOL}{self.DATA_BUCKET}/{self.DATA_DIR}"

    @property
    def data_org_s3_prefix(self) -> str:
        return f"{self.S3_PROTOCOL}{self.bucket_name}/{self.data_org_prefix}"

    @property
    def data_s3_prefix(self) -> str:
        return f"{self.S3_PROTOCOL}{self.bucket_name}/{self.data_prefix}"

    @property
    def users_s3_prefix(self) -> str:
        return f"{self.S3_PROTOCOL}{self.bucket_name}/{self.users_prefix}"

    def uri_ok(self, path: Optional[str]) -> bool:
        return path is not None and path.startswith(self.EXPLORER_SCHEME)

    def translate_path_to_s3_path(self, path: Optional[str]) -> Optional[str]:
        """Accepts any input path and converts `e://` path to `s3://` path if input is an
        `e://` path

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
            path_remainder = "/".join(path_noprefix_split[1:])
            if namespace == self.USERS:
                if len(path_noprefix_split) <= 1:
                    raise ValueError(f"A user id (or '{self.ME}') must be specified")
                user_id = path_noprefix_split[1]
                if user_id != self.ME:
                    try:
                        uuid.UUID(user_id)
                    except ValueError:
                        raise ValueError(
                            f"User id '{user_id}' is not a valid UUID (or '{self.ME}')"
                        )
                path_remainder = "/".join(path_noprefix_split[2:])
            path = f"{self.data_s3_prefix}/{path_remainder}"
        return path

    def execute_aws_s3_path(
        self,
        cmd: str,
        path: str,
        args: List[str],
    ) -> None:
        """Executes the respective `aws s3` single-path commands with `e://` paths
        translated to `s3://` paths"""
        if not self.uri_ok(path):
            raise ValueError(f"Path {path} does not start with {self.EXPLORER_SCHEME}")
        sh.aws.s3(
            cmd,
            self.translate_path_to_s3_path(path),
            *args,
            _in=sys.stdin,
            _out=sys.stdout,
            _err=sys.stderr,
            _env=self.aws_env,
        )
