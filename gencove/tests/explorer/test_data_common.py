from unittest.mock import patch

import pytest
from gencove.command.explorer.data.common import GencoveExplorerManager, AWSCredentials


class TestGencoveExplorerManager:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.user_id = "11111111-1111-1111-1111-111111111111"
        self.organization_id = "11111111-1111-1111-1111-111111111111"
        self.org_id_short = self.organization_id.replace("-", "")[:12]
        self.mock_aws_credentials = AWSCredentials(
            access_key="mock_access", secret_key="mock_secret", token="mock_token"
        )
        self.explorer_manager = GencoveExplorerManager(
            aws_session_credentials=self.mock_aws_credentials,
            user_id=self.user_id,
            organization_id=self.organization_id,
        )

    def test_bucket_name(self):
        assert (
            self.explorer_manager.bucket_name == f"gencove-explorer-{self.org_id_short}"
        )

    def test_users_prefix(self):
        assert self.explorer_manager.users_prefix == "users"

    def test_base_prefix(self):
        expected_prefix = f"users/{self.user_id}"
        assert self.explorer_manager.base_prefix == expected_prefix

    def test_shared_prefix(self):
        assert self.explorer_manager.shared_prefix == "shared"

    def test_data_org_prefix(self):
        expected_prefix = "shared/files"
        assert self.explorer_manager.data_org_prefix == expected_prefix

    def test_data_prefix(self):
        expected_prefix = f"users/{self.user_id}/files"
        assert self.explorer_manager.data_prefix == expected_prefix

    def test_user_prefix(self):
        expected_prefix = f"users/{self.user_id}/files"
        assert self.explorer_manager.user_prefix == expected_prefix

    def test_tmp_prefix(self):
        expected_prefix = f"users/{self.user_id}/files/tmp"
        assert self.explorer_manager.tmp_prefix == expected_prefix

    def test_tmp_org_prefix(self):
        expected_prefix = "shared/files/tmp"
        assert self.explorer_manager.tmp_org_prefix == expected_prefix

    def test_scratch_prefix(self):
        expected_prefix = f"users/{self.user_id}/scratch"
        assert self.explorer_manager.scratch_prefix == expected_prefix

    def test_user_scratch_s3_prefix(self):
        expected_prefix = (
            f"s3://gencove-explorer-{self.org_id_short}/users/{self.user_id}/scratch"
        )
        assert self.explorer_manager.user_scratch_s3_prefix == expected_prefix

    def test_shared_org_s3_prefix(self):
        expected_prefix = f"s3://gencove-explorer-{self.org_id_short}/shared"
        assert self.explorer_manager.shared_org_s3_prefix == expected_prefix

    def test_data_gencove_s3_prefix(self):
        expected_prefix = "s3://gencove-explorer-data/files"
        assert self.explorer_manager.data_gencove_s3_prefix == expected_prefix

    def test_data_org_s3_prefix(self):
        expected_prefix = f"s3://gencove-explorer-{self.org_id_short}/shared/files"
        assert self.explorer_manager.data_org_s3_prefix == expected_prefix

    def test_data_s3_prefix(self):
        expected_prefix = (
            f"s3://gencove-explorer-{self.org_id_short}/users/{self.user_id}/files"
        )
        assert self.explorer_manager.data_s3_prefix == expected_prefix

    def test_users_s3_prefix(self):
        expected_prefix = f"s3://gencove-explorer-{self.org_id_short}/users"
        assert self.explorer_manager.users_s3_prefix == expected_prefix

    def test_aws_env(self):
        expected = {
            "AWS_ACCESS_KEY_ID": "mock_access",
            "AWS_SECRET_ACCESS_KEY": "mock_secret",
            "AWS_SESSION_TOKEN": "mock_token",
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
        assert self.explorer_manager.uri_ok(path) == expected

    def test_translate_path_to_s3_path_valid(self):
        translated_path = self.explorer_manager.translate_path_to_s3_path(
            path="e://users/me"
        )
        assert (
            translated_path
            == "s3://gencove-explorer-111111111111/users/11111111-1111-1111-1111-111111111111/files/"
        )  # noqa: E501

    def test_translate_path_to_s3_path_invalid(self):
        # Test with an invalid e:// path and expect a ValueError
        with pytest.raises(ValueError):
            self.explorer_manager.translate_path_to_s3_path("e://invalid/path")

    @patch("gencove.command.explorer.data.common.GencoveExplorerManager.list_users")
    def test_list_users(self, mock_list_users):
        mock_list_users.return_value = "user1\nuser2"
        self.explorer_manager.list_users()
        mock_list_users.assert_called_once()

    @patch("gencove.command.explorer.data.common.sh.aws")
    def test_execute_aws_s3_src_dst(self, mocked_aws):
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

    @patch("gencove.command.explorer.data.common.sh.aws")
    def test_execute_aws_s3_src_dst_invalid_path(self, mocked_aws):
        cmd = "cp"
        source = "invalid"
        destination = "invalid"
        args = ["--arg1", "--arg2"]

        with pytest.raises(ValueError):
            self.explorer_manager.execute_aws_s3_src_dst(cmd, source, destination, args)

    @patch("gencove.command.explorer.data.common.sh.aws")
    def test_execute_execute_aws_s3_path(self, mocked_aws):
        cmd = "cp"
        path = "e://users/me/source"
        args = ["--arg1", "--arg2"]

        translated_path = self.explorer_manager.translate_path_to_s3_path(path)

        s3_cmd = self.explorer_manager.execute_aws_s3_path(cmd, path, args)

        assert s3_cmd == [cmd, translated_path, *args]

    @patch("gencove.command.explorer.data.common.sh.aws")
    def test_execute_execute_aws_s3_path_invalid_path(self, mocked_aws):
        cmd = "cp"
        path = "invalid"
        args = ["--arg1", "--arg2"]

        with pytest.raises(ValueError):
            self.explorer_manager.execute_aws_s3_path(cmd, path, args)
