"""Common code shared across data commands is stored here"""
import os
import re
import subprocess  # nosec B404 (bandit subprocess import)
import sys
import uuid
from dataclasses import dataclass
from typing import List, Optional, Tuple

import boto3

# pylint: disable=wrong-import-order
from gencove.collections_extras import LazyList
from gencove.exceptions import ValidationError  # noqa I100
from gencove.logger import echo_error
from gencove.models import (
    ExplorerDataCredentials,
    OrganizationUser,
)


@dataclass
class GencoveExplorerManager:  # pylint: disable=too-many-instance-attributes,too-many-public-methods # noqa: E501
    """Port of Explorer GencoveClient and related functionality"""

    user_id: str
    organization_id: str

    aws_session_credentials: Optional[ExplorerDataCredentials]
    organization_users: LazyList[OrganizationUser]

    # Constants ported from Gencove Explorer package
    # https://gitlab.com/gencove/platform/explorer-sdk/-/blob/main/gencove_explorer/constants.py  # noqa: E501 # pylint: disable=line-too-long
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
        aws_env = {}
        if self.aws_session_credentials:
            aws_env = {
                "AWS_ACCESS_KEY_ID": self.aws_session_credentials.access_key,
                "AWS_SECRET_ACCESS_KEY": self.aws_session_credentials.secret_key,
                "AWS_SESSION_TOKEN": self.aws_session_credentials.token,
                "AWS_DEFAULT_REGION": self.aws_session_credentials.region_name,
                "AWS_REGION": self.aws_session_credentials.region_name,
            }
        return aws_env

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

    def run_s3_command(self, s3_command: List[str]) -> None:
        """Run AWS S3 command while handling AWS CLI non-zero exits gracefully

        Args:
            s3_command (List[str]): List of arguments to pass to AWS CLI
        """
        command = ["aws", "s3"] + s3_command
        env = os.environ.copy()
        env.update(self.aws_env)
        try:
            subprocess.run(  # nosec B603 (execution of untrusted input)
                command,
                stdin=sys.stdin,
                stdout=sys.stdout,
                stderr=sys.stderr,
                env=env,
                check=True,
            )
        except subprocess.CalledProcessError as err:
            if err.stderr:
                echo_error(err.stderr.decode())  # pylint: disable=no-member
            sys.exit(err.returncode)

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
        e://users/<user-email>/...

        Args:
            path (Optional[str]): Path to convert

        Returns:
            Converted path
        """
        if path is None:
            return None
        if path.startswith(self.EXPLORER_SCHEME):
            path_noprefix = path[len(self.EXPLORER_SCHEME) :]  # noqa: E203
            path_noprefix_split = path_noprefix.split("/")
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
                        # check to see if the user supplied email instead of user_id
                        if is_valid_email(user_id):
                            # only open client with valid email
                            user_id = email2uid(user_id, self.organization_users)
                        else:
                            raise ValueError(  # pylint: disable=raise-missing-from
                                f"User id '{user_id}' is not a valid UUID, email, nor '{self.ME}'"  # noqa E501
                            )
                    prefix_s3 = self.users_s3_prefix + f"/{user_id}/{self.USER_DIR}"
                path_remainder = "/".join(path_noprefix_split[2:])
            path = f"{prefix_s3}/{path_remainder}"
        return path

    # pylint: disable=too-many-locals
    def list_users(self):
        """List e:// user dir"""
        user_prefix = f"{self.S3_PROTOCOL}{self.bucket_name}/{self.USERS_DIR}/"
        command = ["aws", "s3", "ls", user_prefix]
        env = os.environ.copy()
        env.update(self.aws_env)
        try:
            # list that serves to preserve the order of user_ids from s3api
            s3api_uids = []
            result = subprocess.run(  # nosec B603 (execution of untrusted input)
                command,
                stdin=sys.stdin,
                stdout=subprocess.PIPE,
                stderr=sys.stderr,
                env=env,
                check=True,
                text=True,
            )

            # iterate across s3_uids returned by s3api
            for line in result.stdout.splitlines():
                s3_uid = line.split("PRE ")[1].split("/")[0]
                # translate user_id to email
                email = uid2email(s3_uid, self.organization_users)
                if email is not None:
                    s3api_uids.append({"id": s3_uid, "email": email})  # noqa E501

            # maximum email length in set
            max_email_length = max(len(item["email"]) for item in s3api_uids)

            for item in s3api_uids:
                email = item["email"]
                user_id = item["id"]
                # Format the string such that the email is
                # left-aligned with padding to the maximum length
                spacing = " " * 27
                formatted_string = (
                    f"{spacing}PRE {email:<{max_email_length}} ({user_id}/)\n"
                )
                sys.stdout.write(formatted_string)

        except subprocess.CalledProcessError as err:
            sys.stderr.write(f"Error listing users: {err}\n")
            sys.exit(err.returncode)

    def execute_aws_s3_path(
        self,
        cmd: str,
        path: str,
        args: List[str],
    ) -> List[str]:
        """Executes the respective `aws s3` single-path commands with `e://` paths
        translated to `s3://` paths

        Args:
            cmd (str): AWS S3 command to execute
            path (str): Path to execute command against
            args (List[str]): List of additional args to forward to AWS CLI
            organization_user (List[OrganizationUser]): List to map email to user_id

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
        self.run_s3_command(s3_command)
        return s3_command

    def execute_aws_s3_src_dst(
        self, cmd: str, source: str, destination: str, args: List[str]
    ) -> List[str]:
        """Executes the respective `aws s3` dual-path (source-to-destination)
        commands with e://` paths translated to `s3://` paths

        Args:
            cmd (str): AWS S3 command to execute
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
        self.run_s3_command(s3_command)
        return s3_command

    def thread_safe_client(self, service_name, *args, **kwargs):
        """Thread safe boto client with explorer session credentials.

        Args:
            service_name (str): Name of the service.

        Returns:
            BotoClient: Thread safe client.
        """
        # Thread-safe, as per:
        # https://boto3.amazonaws.com/v1/documentation/api/1.17.90/guide/clients.html#multithreading-or-multiprocessing-with-clients
        if self.aws_session_credentials:
            boto_session = boto3.Session(
                aws_access_key_id=self.aws_session_credentials.access_key,
                aws_secret_access_key=self.aws_session_credentials.secret_key,
                aws_session_token=self.aws_session_credentials.token,
                region_name=self.aws_session_credentials.region_name,
            )
        else:
            boto_session = boto3.Session()
        return boto_session.client(service_name, *args, **kwargs)

    def list_s3_objects(self, path: str):
        """List S3 objects in given path.

        Args:
            path (str): Path to s3 objects.

        Returns:
            PaginatedResponse: List of objects paginated.
        """
        s3_client = self.thread_safe_client("s3")
        s3_path = self.translate_path_to_s3_path(path)
        bucket, prefix = s3_path.lstrip("s3://").split("/", 1)
        paginated_response = s3_client.get_paginator("list_objects_v2").paginate(
            Bucket=bucket,
            Prefix=prefix,
            PaginationConfig={
                "PageSize": 1_000,
            },
        )
        return paginated_response


def validate_explorer_user_data(
    user: uuid.UUID, organization: uuid.UUID, explorer_enabled: bool
):
    """Validate user and organization data

    Args:
        user_id (uuid.UUID): User id
        organization_id (uuid.UUID): Organization id
        explorer_enabled (bool): Wether explorer is enabled for the current user
    """
    if not explorer_enabled:
        raise ValidationError(
            "Explorer is not enabled on your user account, quitting. "
            "Please reach out to your organization owner to inquire "
            "about Gencove Explorer."
        )

    if not user or not organization:
        raise ValidationError("Could not retrieve user details, quitting.")


def request_is_from_explorer() -> bool:
    """
    Detects whether user is executing code from an Explorer environment.
    If check fails, we assume user is not in environment.

    Returns:
        bool: True if user in Explorer environment, False otherwise
    """
    try:
        user_id = os.environ.get("GENCOVE_USER_ID", None)
        if user_id is None:
            return False
        user_id_dashes = str(uuid.UUID(user_id))
        expected_role_name_instance = f"explorer-user-{user_id}-role"
        expected_role_name_cluster = f"explorer-{user_id_dashes}-ecs_task_role"
        client = boto3.client("sts")
        response = client.get_caller_identity()
        if (
            expected_role_name_instance in response["Arn"]
            or expected_role_name_cluster in response["Arn"]
        ):
            return True
    except Exception:  # noqa pylint: disable=broad-except
        return False
    return False


def uid2email(
    uid: str, organization_users: List[OrganizationUser], no_match_value=None
) -> str:
    """
    Convert gencove user-id to corresponding email address

    Args:
        uid (str): gencove user-id (assumption: in gencove organization)
        organization_users(List[dict]): payload from organization-users endpoint.
        no_match_value: default None; value returned if no email matches uid.

    Returns:
        str: email corresponding to user_id, otherwise no_match_value
    """
    dict_match = next(
        (item for item in organization_users if str(item.id) == uid), no_match_value
    )  # noqa E501
    if dict_match is not no_match_value:
        return dict_match.email
    return no_match_value


def email2uid(
    email: str, organization_users: List[OrganizationUser], no_match_value=None
) -> str:
    """
    Convert gencove user_id to corresponding email address

    Args:
        email (str): gencove email (assumption: in gencove organization)
        organization_users(List[dict]): payload from organization-users endpoint.
        no_match_value: default None; value returned if no user_id matches email.

    Returns:
        str: user_id corresponding to email, otherwise no_match_value
    """
    dict_match = next(
        (item for item in organization_users if item.email == email), no_match_value
    )  # noqa E501
    if dict_match is not no_match_value:
        return dict_match.id
    return no_match_value


def is_valid_email(input_string) -> bool:
    """
    Base check for whether an input string is an email address

    returns: True if input string looks like an email, otherwise False
    """
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return bool(re.match(pattern, input_string))
