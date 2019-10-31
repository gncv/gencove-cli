"""Tests upload command of Gencove CLI."""
import os

from click.testing import CliRunner

from gencove.cli import upload
from gencove.client import APIClient
from gencove.command.upload.constants import UPLOAD_PREFIX


def test_upload(mocker):
    """Sanity check that upload is ok."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        os.mkdir("cli_test_data")
        with open("cli_test_data/test.fastq.gz", "w") as fastq_file:
            fastq_file.write("AAABBB")

        mocked_login = mocker.patch.object(
            APIClient, "login", return_value=None
        )
        mocked_get_credentials = mocker.patch(
            "gencove.command.upload.main.get_s3_client_refreshable"
        )
        mocked_get_upload_details = mocker.patch.object(
            APIClient,
            "get_upload_details",
            return_value={
                "last_status": {"status": ""},
                "s3": {"bucket": "test", "object_name": "test"},
            },
        )
        mocked_upload_file = mocker.patch(
            "gencove.command.upload.main.upload_file"
        )
        res = runner.invoke(
            upload,
            ["cli_test_data"],
            input="\n".join(["foo@bar.com", "123456"]),
        )
        # for debugging, if needed
        print("output is", res.output)

        assert res.exit_code == 0
        mocked_login.assert_called_once()
        mocked_get_credentials.assert_called_once()
        mocked_get_upload_details.assert_called_once()
        mocked_upload_file.assert_called_once()


def test_upload_no_files_found(mocker):
    """Test that no fastq files found exits upload."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        os.mkdir("cli_test_data")

        mocked_login = mocker.patch.object(
            APIClient, "login", return_value=None
        )
        res = runner.invoke(
            upload,
            ["cli_test_data"],
            input="\n".join(["foo@bar.com", "123456"]),
        )
        # for debugging, if needed
        print("output is", res.output)

        assert res.exit_code == 0
        assert "No FASTQ files found in the path" in res.output
        mocked_login.assert_called_once()


def test_upload_invalid_destination(mocker):
    """Test that invalid destination exists upload."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        os.mkdir("cli_test_data")
        with open("cli_test_data/test.fastq.gz", "w") as fastq_file:
            fastq_file.write("AAABBB")

        mocked_login = mocker.patch.object(
            APIClient, "login", return_value=None
        )
        res = runner.invoke(
            upload,
            ["cli_test_data", "foobar_dir"],
            input="\n".join(["foo@bar.com", "123456"]),
        )
        # for debugging, if needed
        print("output is", res.output)

        assert res.exit_code == 0
        assert (
            "Invalid destination path. Must start with '{}'".format(
                UPLOAD_PREFIX
            )
            in res.output
        )
        mocked_login.assert_called_once()


def test_upload_and_run_immediately(mocker):
    """Upload and assign right away."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        os.mkdir("cli_test_data")
        with open("cli_test_data/test.fastq.gz", "w") as fastq_file:
            fastq_file.write("AAABBB")

        mocked_login = mocker.patch.object(
            APIClient, "login", return_value=None
        )
        mocked_get_credentials = mocker.patch(
            "gencove.command.upload.main.get_s3_client_refreshable"
        )
        mocked_get_upload_details = mocker.patch.object(
            APIClient,
            "get_upload_details",
            return_value={
                "id": "test",
                "last_status": {"status": ""},
                "s3": {"bucket": "test", "object_name": "test"},
            },
        )
        mocked_upload_file = mocker.patch(
            "gencove.command.upload.main.upload_file"
        )
        mocked_get_sample_sheet = mocker.patch.object(
            APIClient,
            "get_sample_sheet",
            return_value={
                "meta": {"next": None},
                "results": [
                    {"client_id": "foo", "fastq": {"r1": {"upload": "test"}}}
                ],
            },
        )
        mocked_assign_sample = mocker.patch.object(
            APIClient, "add_samples_to_project", return_value={}
        )

        res = runner.invoke(
            upload,
            [
                "cli_test_data",
                "--email",
                "foo@bar.com",
                "--password",
                "123456",
                "--run-project-id",
                "1234",
            ],
        )

        assert res.exit_code == 0
        mocked_login.assert_called_once()
        mocked_get_credentials.assert_called_once()
        mocked_get_upload_details.assert_called_once()
        mocked_upload_file.assert_called_once()
        mocked_get_sample_sheet.assert_called()
        mocked_assign_sample.assert_called_once()


def test_upload_and_run_immediately_something_went_wrong(mocker):
    """Upload and assign right away did't work."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        os.mkdir("cli_test_data")
        with open("cli_test_data/test.fastq.gz", "w") as fastq_file:
            fastq_file.write("AAABBB")

        mocked_login = mocker.patch.object(
            APIClient, "login", return_value=None
        )
        mocked_get_credentials = mocker.patch(
            "gencove.command.upload.main.get_s3_client_refreshable"
        )
        mocked_get_upload_details = mocker.patch.object(
            APIClient,
            "get_upload_details",
            return_value={
                "id": "test",
                "last_status": {"status": ""},
                "s3": {"bucket": "test", "object_name": "test"},
            },
        )
        mocked_upload_file = mocker.patch(
            "gencove.command.upload.main.upload_file"
        )
        mocked_get_sample_sheet = mocker.patch.object(
            APIClient,
            "get_sample_sheet",
            return_value={"meta": {"next": None}, "results": []},
        )
        mocked_assign_sample = mocker.patch.object(
            APIClient, "add_samples_to_project", return_value={}
        )

        res = runner.invoke(
            upload,
            [
                "cli_test_data",
                "--email",
                "foo@bar.com",
                "--password",
                "123456",
                "--run-project-id",
                "1234",
            ],
        )

        assert res.exit_code == 0
        mocked_login.assert_called_once()
        mocked_get_credentials.assert_called_once()
        mocked_get_upload_details.assert_called_once()
        mocked_upload_file.assert_called_once()
        mocked_get_sample_sheet.assert_called()
        mocked_assign_sample.assert_not_called()
