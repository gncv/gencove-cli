"""Tests upload command of Gencove CLI."""
import io
import json
import os
import sys
from uuid import uuid4

from click import echo
from click.testing import CliRunner

from gencove.cli import upload
from gencove.client import APIClient, APIClientTimeout
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

        assert res.exit_code == 0
        mocked_login.assert_called_once()
        mocked_get_credentials.assert_called_once()
        mocked_get_upload_details.assert_called_once()
        mocked_upload_file.assert_called_once()
        assert not mocked_upload_file.call_args[1]["no_progress"]


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

        assert res.exit_code == 1
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

        assert res.exit_code == 1
        assert (
            "Invalid destination path. Must start with '{}'".format(
                UPLOAD_PREFIX
            )
            in res.output
        )
        mocked_login.assert_called_once()


def test_upload_project_id_not_uuid(mocker):
    """Test that project id is valid UUID when uploading."""
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

        assert res.exit_code == 1
        assert "--run-project-id is not valid" in res.output
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
        mocked_regular_progress_bar = mocker.patch(
            "gencove.command.upload.main.get_regular_progress_bar"
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
                "11111111-1111-1111-1111-111111111111",
            ],
        )

        assert res.exit_code == 0
        mocked_login.assert_called_once()
        mocked_get_credentials.assert_called_once()
        mocked_get_upload_details.assert_called_once()
        mocked_upload_file.assert_called_once()
        mocked_get_sample_sheet.assert_called()
        mocked_assign_sample.assert_called_once()
        mocked_regular_progress_bar.assert_called_once()


def test_upload_and_run_immediately__with_metadata(mocker):
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
        mocked_regular_progress_bar = mocker.patch(
            "gencove.command.upload.main.get_regular_progress_bar"
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
                "11111111-1111-1111-1111-111111111111",
                "--metadata",
                "[1,2]",
            ],
        )

        assert res.exit_code == 0
        mocked_login.assert_called_once()
        mocked_get_credentials.assert_called_once()
        mocked_get_upload_details.assert_called_once()
        mocked_upload_file.assert_called_once()
        mocked_get_sample_sheet.assert_called()
        mocked_assign_sample.assert_called_once()
        mocked_regular_progress_bar.assert_called_once()


def test_upload_and_run_immediately__invalid_metadata(mocker):
    """Upload and assign right away with invalid metadata."""
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
                "11111111-1111-1111-1111-111111111111",
                "--metadata",
                "[1,2,3",
            ],
        )

        assert res.exit_code == 1
        mocked_login.assert_called_once()
        mocked_get_credentials.assert_not_called()
        mocked_get_upload_details.assert_not_called()
        mocked_upload_file.assert_not_called()
        mocked_get_sample_sheet.assert_not_called()
        mocked_assign_sample.assert_not_called()
        assert "--metadata is not valid JSON" in res.output


def test_upload__with_metadata_without_project_id(mocker):
    """Test that project id is present if attaching metadata when
    uploading."""
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
            [
                "cli_test_data",
                "--email",
                "foo@bar.com",
                "--password",
                "123456",
                "--metadata",
                "[1,2]",
            ],
        )

        assert res.exit_code == 1
        assert (
            "--metadata cannot be used without --run-project-id" in res.output
        )
        mocked_login.assert_called_once()


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
                "11111111-1111-1111-1111-111111111111",
            ],
        )

        assert res.exit_code == 0
        mocked_login.assert_called_once()
        mocked_get_credentials.assert_called_once()
        mocked_get_upload_details.assert_called_once()
        mocked_upload_file.assert_called_once()
        mocked_get_sample_sheet.assert_called()
        mocked_assign_sample.assert_not_called()


def test_upload_and_run_immediately_with_output_to_file(mocker):
    """Upload and assign right away, then save results to a file."""
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
        upload_id = str(uuid4())
        sample_id = str(uuid4())
        mocked_response = [
            {
                "client_id": "foo",
                "fastq": {"r1": {"upload": upload_id}},
                "sample": sample_id,
            }
        ]
        mocked_assign_sample = mocker.patch.object(
            APIClient, "add_samples_to_project", return_value=mocked_response
        )

        mocker.patch("gencove.command.upload.main.get_regular_progress_bar")
        res = runner.invoke(
            upload,
            [
                "cli_test_data",
                "--email",
                "foo@bar.com",
                "--password",
                "123456",
                "--run-project-id",
                "11111111-1111-1111-1111-111111111111",
                "--output",
                "samples.json",
            ],
        )

        assert res.exit_code == 0
        mocked_login.assert_called_once()
        mocked_get_credentials.assert_called_once()
        mocked_get_upload_details.assert_called_once()
        mocked_upload_file.assert_called_once()
        mocked_get_sample_sheet.assert_called()
        mocked_assign_sample.assert_called_once()
        output_content = None
        with open("samples.json", "r") as output_file:
            output_content = output_file.read()
        assert json.dumps(mocked_response, indent=4) == output_content


def test_upload_and_run_immediately_with_output_to_nested_file(mocker):
    """Upload and assign right away, then save results to a file."""
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
        upload_id = str(uuid4())
        sample_id = str(uuid4())
        mocked_response = [
            {
                "client_id": "foo",
                "fastq": {"r1": {"upload": upload_id}},
                "sample": sample_id,
            }
        ]
        mocked_assign_sample = mocker.patch.object(
            APIClient, "add_samples_to_project", return_value=mocked_response
        )

        mocker.patch("gencove.command.upload.main.get_regular_progress_bar")
        res = runner.invoke(
            upload,
            [
                "cli_test_data",
                "--email",
                "foo@bar.com",
                "--password",
                "123456",
                "--run-project-id",
                "11111111-1111-1111-1111-111111111111",
                "--output",
                "somefolder/samples.json",
            ],
        )

        assert res.exit_code == 0
        mocked_login.assert_called_once()
        mocked_get_credentials.assert_called_once()
        mocked_get_upload_details.assert_called_once()
        mocked_upload_file.assert_called_once()
        mocked_get_sample_sheet.assert_called()
        mocked_assign_sample.assert_called_once()
        with open("somefolder/samples.json", "r") as output_file:
            output_content = output_file.read()
        assert json.dumps(mocked_response, indent=4) == output_content


def test_upload_and_run_immediately_with_stdout(mocker):
    """Upload and assign right away, then print out the results."""
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
        upload_id = str(uuid4())
        sample_id = str(uuid4())
        mocked_response = [
            {
                "client_id": "foo",
                "fastq": {"r1": {"upload": upload_id}},
                "sample": sample_id,
            }
        ]
        mocked_assign_sample = mocker.patch.object(
            APIClient, "add_samples_to_project", return_value=mocked_response
        )

        mocker.patch("gencove.command.upload.main.get_regular_progress_bar")

        res = runner.invoke(
            upload,
            [
                "cli_test_data",
                "--email",
                "foo@bar.com",
                "--password",
                "123456",
                "--run-project-id",
                "11111111-1111-1111-1111-111111111111",
                "--output",
                "-",
            ],
        )

        assert res.exit_code == 0
        mocked_login.assert_called_once()
        mocked_get_credentials.assert_called_once()
        mocked_get_upload_details.assert_called_once()
        mocked_upload_file.assert_called_once()
        mocked_get_sample_sheet.assert_called()
        mocked_assign_sample.assert_called_once()
        output_line = io.BytesIO()
        sys.stdout = output_line
        echo(json.dumps(mocked_response, indent=4))
        assert output_line.getvalue() in res.output.encode()


def test_upload_without_progressbar(mocker):
    """Upload do not show the progress bar."""
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

        res = runner.invoke(
            upload,
            [
                "cli_test_data",
                "--email",
                "foo@bar.com",
                "--password",
                "123456",
                "--no-progress",
            ],
        )

        assert res.exit_code == 0
        mocked_login.assert_called_once()
        mocked_get_credentials.assert_called_once()
        mocked_get_upload_details.assert_called_once()
        mocked_upload_file.assert_called_once()
        assert mocked_upload_file.call_args[1]["no_progress"]


def test_upload_and_run_immediately_without_progressbar(mocker):
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
        mocked_regular_progress_bar = mocker.patch(
            "gencove.command.upload.main.get_regular_progress_bar"
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
                "11111111-1111-1111-1111-111111111111",
                "--no-progress",
            ],
        )

        assert res.exit_code == 0
        mocked_login.assert_called_once()
        mocked_get_credentials.assert_called_once()
        mocked_get_upload_details.assert_called_once()
        mocked_upload_file.assert_called_once()
        mocked_get_sample_sheet.assert_called()
        mocked_assign_sample.assert_called_once()
        mocked_regular_progress_bar.assert_not_called()


def test_upload_and_run_immediately_slow_response_retry(mocker):
    """Upload and assign right away and retry on slow response."""
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
            side_effect=APIClientTimeout(
                "Could not connect to the api server"
            ),
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
                "11111111-1111-1111-1111-111111111111",
                "--no-progress",
            ],
        )

        assert res.exit_code == 0
        mocked_login.assert_called_once()
        mocked_get_credentials.assert_called_once()
        mocked_get_upload_details.assert_called_once()
        mocked_upload_file.assert_called_once()
        assert mocked_get_sample_sheet.call_count == 5
        assert "there was an error automatically running them" in res.output
