"""Tests for command.explorer.data.common"""
import os
import uuid
from unittest import TestCase
from unittest.mock import MagicMock, patch

# pylint: disable=wrong-import-order, import-error

import pytest

from gencove.command.explorer.data.common import (  # noqa: I100
    ExplorerDataCredentials,
    GencoveExplorerManager,
    request_is_from_explorer,
)
from gencove.tests.utils import MOCK_UUID


class TestGencoveExplorerManager:  # pylint: disable=too-many-public-methods
    """Test GencoveExplorerManager"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Initialize mocked instance of GencoveExplorerManager"""
        # pylint: disable=attribute-defined-outside-init
        self.user_id = "11111111-1111-1111-1111-111111111111"
        self.organization_id = "11111111-1111-1111-1111-111111111111"
        self.org_id_short = self.organization_id.replace("-", "")[:12]
        self.mock_aws_credentials = ExplorerDataCredentials(
            access_key="mock_access",
            secret_key="mock_secret",
            token="mock_token",
            region_name="mock_region",
        )
        self.explorer_manager = GencoveExplorerManager(
            aws_session_credentials=self.mock_aws_credentials,
            user_id=self.user_id,
            organization_id=self.organization_id,
        )

    def test_bucket_name(self):
        """Test bucket_name"""
        assert (
            self.explorer_manager.bucket_name
            == f"gencove-explorer-{self.org_id_short}"  # noqa: E501 pylint: disable=line-too-long
        )

    def test_users_prefix(self):
        """Test users_prefix"""
        assert self.explorer_manager.users_prefix == "users"

    def test_base_prefix(self):
        """Test base_prefix"""
        expected_prefix = f"users/{self.user_id}"
        assert self.explorer_manager.base_prefix == expected_prefix

    def test_shared_prefix(self):
        """Test shared_prefix"""
        assert self.explorer_manager.shared_prefix == "shared"

    def test_data_org_prefix(self):
        """Test data_org_prefix"""
        expected_prefix = "shared/files"
        assert self.explorer_manager.data_org_prefix == expected_prefix

    def test_data_prefix(self):
        """Test data_prefix"""
        expected_prefix = f"users/{self.user_id}/files"
        assert self.explorer_manager.data_prefix == expected_prefix

    def test_user_prefix(self):
        """Test user_prefix"""
        expected_prefix = f"users/{self.user_id}/files"
        assert self.explorer_manager.user_prefix == expected_prefix

    def test_tmp_prefix(self):
        """Test tmp_prefix"""
        expected_prefix = f"users/{self.user_id}/files/tmp"
        assert self.explorer_manager.tmp_prefix == expected_prefix

    def test_tmp_org_prefix(self):
        """Test tmp_org_prefix"""
        expected_prefix = "shared/files/tmp"
        assert self.explorer_manager.tmp_org_prefix == expected_prefix

    def test_scratch_prefix(self):
        """Test scratch_prefix"""
        expected_prefix = f"users/{self.user_id}/scratch"
        assert self.explorer_manager.scratch_prefix == expected_prefix

    def test_user_scratch_s3_prefix(self):
        """Test user_scratch_s3_prefix"""
        expected_prefix = (
            f"s3://gencove-explorer-{self.org_id_short}/users/{self.user_id}/scratch"
        )
        assert self.explorer_manager.user_scratch_s3_prefix == expected_prefix

    def test_shared_org_s3_prefix(self):
        """Test shared_org_s3_prefix"""
        expected_prefix = f"s3://gencove-explorer-{self.org_id_short}/shared"
        assert self.explorer_manager.shared_org_s3_prefix == expected_prefix

    def test_data_gencove_s3_prefix(self):
        """Test data_gencove_s3_prefix"""
        expected_prefix = "s3://gencove-explorer-data/files"
        assert self.explorer_manager.data_gencove_s3_prefix == expected_prefix

    def test_data_org_s3_prefix(self):
        """Test data_org_s3_prefix"""
        expected_prefix = f"s3://gencove-explorer-{self.org_id_short}/shared/files"
        assert self.explorer_manager.data_org_s3_prefix == expected_prefix

    def test_data_s3_prefix(self):
        """Test data_s3_prefix"""
        expected_prefix = (
            f"s3://gencove-explorer-{self.org_id_short}/users/{self.user_id}/files"
        )
        assert self.explorer_manager.data_s3_prefix == expected_prefix

    def test_users_s3_prefix(self):
        """Test users_s3_prefix"""
        expected_prefix = f"s3://gencove-explorer-{self.org_id_short}/users"
        assert self.explorer_manager.users_s3_prefix == expected_prefix

    def test_aws_env(self):
        """Test aws_env"""
        expected = {
            "AWS_ACCESS_KEY_ID": "mock_access",
            "AWS_SECRET_ACCESS_KEY": "mock_secret",
            "AWS_SESSION_TOKEN": "mock_token",
            "AWS_DEFAULT_REGION": "mock_region",
            "AWS_REGION": "mock_region",
        }
        assert self.explorer_manager.aws_env == expected

    @pytest.mark.parametrize(
        "path, expected",
        [
            ("e://path", True),
            (None, False),
            ("invalid://path", False),
            ("s3://bucket/path", False),
        ],
    )
    def test_uri_ok(self, path, expected):
        """Test uri_ok()"""
        assert self.explorer_manager.uri_ok(path) == expected

    def test_translate_path_to_s3_path_valid(self):
        """Test translate_path_to_s3_path"""
        translated_path = self.explorer_manager.translate_path_to_s3_path(
            path="e://users/me"
        )
        assert (
            translated_path
            == f"s3://gencove-explorer-{self.org_id_short}/users/{self.organization_id}/files/"  # noqa: E501 pylint: disable=line-too-long
        )  # noqa: E501

    def test_translate_path_to_s3_path_invalid(self):
        """Test with an invalid e:// path and expect a ValueError"""
        with pytest.raises(ValueError):
            self.explorer_manager.translate_path_to_s3_path("e://invalid/path")

    @patch("gencove.command.explorer.data.common.GencoveExplorerManager.list_users")
    def test_list_users(self, mock_list_users):
        """Test list_users()"""
        mock_list_users.return_value = "user1\nuser2"
        self.explorer_manager.list_users()
        mock_list_users.assert_called_once()

    @patch("gencove.command.explorer.data.common.sh.aws", create=True)
    def test_execute_aws_s3_src_dst(self, mocked_aws):  # pylint: disable= W0613
        """Test execute_aws_s3_src_dst()"""
        cmd = "cp"
        source = "e://users/me/source"
        destination = "e://users/me/destination"
        args = ["--arg1", "--arg2"]

        translated_source = self.explorer_manager.translate_path_to_s3_path(source)
        translated_destination = self.explorer_manager.translate_path_to_s3_path(
            destination
        )

        s3_cmd = self.explorer_manager.execute_aws_s3_src_dst(
            cmd, source, destination, args
        )

        assert s3_cmd == [cmd, translated_source, translated_destination, *args]

    @patch("gencove.command.explorer.data.common.sh.aws", create=True)
    def test_execute_aws_s3_src_dst_invalid_path(
        self, mocked_aws
    ):  # noqa: E501 pylint: disable=W0613
        """Test execute_aws_s3_src_dst() with invalid src and dst"""
        cmd = "cp"
        source = "invalid"
        destination = "invalid"
        args = ["--arg1", "--arg2"]

        with pytest.raises(ValueError):
            self.explorer_manager.execute_aws_s3_src_dst(cmd, source, destination, args)

    @patch("gencove.command.explorer.data.common.sh.aws", create=True)
    def test_execute_execute_aws_s3_path(self, mocked_aws):  # pylint: disable=W0613
        """Test execute_aws_s3_path()"""
        cmd = "cp"
        path = "e://users/me/source"
        args = ["--arg1", "--arg2"]

        translated_path = self.explorer_manager.translate_path_to_s3_path(path)

        s3_cmd = self.explorer_manager.execute_aws_s3_path(cmd, path, args)

        assert s3_cmd == [cmd, translated_path, *args]

    @patch("gencove.command.explorer.data.common.sh.aws", create=True)
    def test_execute_execute_aws_s3_path_invalid_path(
        self, mocked_aws
    ):  # noqa: E501 pylint: disable=W0613
        """Test execute_aws_s3_path() with invalid path"""
        cmd = "cp"
        path = "invalid"
        args = ["--arg1", "--arg2"]

        with pytest.raises(ValueError):
            self.explorer_manager.execute_aws_s3_path(cmd, path, args)


class TestRequestIsFromExplorerInstance(TestCase):
    """Test case for request_is_from_instance()"""

    def setUp(self):
        self.user_id = MOCK_UUID
        self.account_id = "123412341234"

    def test_from_explorer_instance(self):
        """Test when request issued from explorer instance"""
        with patch(
            "gencove.command.explorer.data.common.boto3.client"
        ) as mock_boto3, patch.dict(os.environ, {"GENCOVE_USER_ID": self.user_id}):
            client_mock = MagicMock()
            client_mock.get_caller_identity.return_value = {
                "Arn": f"arn:aws:iam::{self.account_id}:role/explorer-user-{self.user_id}-role"  # noqa: E501 pylint: disable=line-too-long
            }
            mock_boto3.return_value = client_mock

            assert request_is_from_explorer() is True

    def test_from_explorer_cluster(self):
        """Test when request issued from explorer cluster"""
        with patch(
            "gencove.command.explorer.data.common.boto3.client"
        ) as mock_boto3, patch.dict(os.environ, {"GENCOVE_USER_ID": self.user_id}):
            user_id_dashes = str(uuid.UUID(self.user_id))
            client_mock = MagicMock()
            client_mock.get_caller_identity.return_value = {
                "Arn": f"arn:aws:iam::{self.account_id}:role/explorer-{user_id_dashes}-ecs_task_role"  # noqa: E501 pylint: disable=line-too-long
            }
            mock_boto3.return_value = client_mock

            assert request_is_from_explorer() is True

    def test_not_from_explorer(self):
        """Test when request not from explorer instance"""
        with patch(
            "gencove.command.explorer.data.common.boto3.client"
        ) as mock_boto3, patch.dict(os.environ, {"GENCOVE_USER_ID": self.user_id}):
            client_mock = MagicMock()
            client_mock.get_caller_identity.return_value = {
                "Arn": "arn:aws:iam::1111111111111111:role/some-other-role"
            }
            mock_boto3.return_value = client_mock

            assert request_is_from_explorer() is False

    def test_exception(self):
        """Test when exception is raised"""
        with patch(
            "gencove.command.explorer.data.common.boto3.client"
        ) as mock_boto3, patch.dict(os.environ, {"GENCOVE_USER_ID": self.user_id}):
            mock_boto3.side_effect = Exception("AWS error")

            assert request_is_from_explorer() is False
