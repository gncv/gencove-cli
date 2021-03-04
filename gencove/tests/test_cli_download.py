"""Test download command."""
import io
import json
import os
import sys
from uuid import uuid4

from click import echo
from click.testing import CliRunner

from gencove.cli import download
from gencove.client import APIClient


def test_no_required_options():
    """Test that command exits without project id or sample id provided."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        os.mkdir("cli_test_data")
        res = runner.invoke(
            download,
            [
                "cli_test_data",
                "--project-id",
                "123",
                "--email",
                "foo@bar.com",
                "--password",
                "12345",
            ],
        )
        assert res.exit_code == 1


def test_both_project_id_and_sample_ids_provided():
    """Command exits if both project id and sample ids are provided."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        os.mkdir("cli_test_data")
        res = runner.invoke(
            download,
            [
                "cli_test_data",
                "--project-id",
                "123",
                "--sample-ids",
                "1,2,3",
                "--email",
                "foo@bar.com",
                "--password",
                "12345",
            ],
        )
    assert res.exit_code == 1


def test_project_id_provided(mocker):
    """Check happy flow."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        mocked_login = mocker.patch.object(
            APIClient, "login", return_value=None
        )
        mocked_project_samples = mocker.patch.object(
            APIClient,
            "get_project_samples",
            return_value={"results": [{"id": 0}], "meta": {"next": None}},
        )
        mocked_sample_details = mocker.patch.object(
            APIClient,
            "get_sample_details",
            return_value={
                "id": 0,
                "client_id": 1,
                "last_status": {
                    "id": str(uuid4()),
                    "status": "succeeded",
                    "created": "2020-07-28T12:46:22.719862Z",
                },
                "archive_last_status": {
                    "id": str(uuid4()),
                    "status": "available",
                    "created": "2020-07-28T12:46:22.719862Z",
                    "transition_cutoff": "2020-08-28T12:46:22.719862Z",
                },
                "files": [
                    {
                        "id": str(uuid4()),
                        "file_type": "txt",
                        "download_url": "https://foo.com/bar.txt",
                    }
                ],
            },
        )
        mocked_qc_metrics = mocker.patch.object(
            APIClient,
            "get_sample_qc_metrics",
            return_value={"results": [{"foo": 12}]},
        )
        mocked_get_metadata = mocker.patch.object(
            APIClient,
            "get_metadata",
            return_value=dict(
                metadata=None,
            ),
        )
        mocked_download_file = mocker.patch(
            "gencove.command.download.main.download_file"
        )
        res = runner.invoke(
            download,
            [
                "cli_test_data",
                "--project-id",
                "123",
                "--email",
                "foo@bar.com",
                "--password",
                "123",
            ],
        )
        assert res.exit_code == 0
        mocked_login.assert_called_once()
        mocked_project_samples.assert_called_once()
        mocked_qc_metrics.assert_called_once()
        mocked_get_metadata.assert_called_once()
        mocked_download_file.assert_called_once()
        mocked_sample_details.assert_called_once()


def test_sample_ids_provided(mocker):
    """Check happy flow with sample ids."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        mocked_login = mocker.patch.object(
            APIClient, "login", return_value=None
        )
        mocked_sample_details = mocker.patch.object(
            APIClient,
            "get_sample_details",
            return_value={
                "id": 0,
                "client_id": 1,
                "last_status": {
                    "id": str(uuid4()),
                    "status": "succeeded",
                    "created": "2020-07-28T12:46:22.719862Z",
                },
                "archive_last_status": {
                    "id": str(uuid4()),
                    "status": "available",
                    "created": "2020-07-28T12:46:22.719862Z",
                    "transition_cutoff": "2020-08-28T12:46:22.719862Z",
                },
                "files": [
                    {
                        "id": str(uuid4()),
                        "file_type": "txt",
                        "download_url": "https://foo.com/bar.txt",
                    }
                ],
            },
        )
        mocked_qc_metrics = mocker.patch.object(
            APIClient,
            "get_sample_qc_metrics",
            return_value={"results": [{"foo": 12}]},
        )
        mocked_get_metadata = mocker.patch.object(
            APIClient,
            "get_metadata",
            return_value=dict(
                metadata=None,
            ),
        )
        mocked_download_file = mocker.patch(
            "gencove.command.download.main.download_file"
        )
        res = runner.invoke(
            download,
            [
                "cli_test_data",
                "--sample-ids",
                "0",
                "--email",
                "foo@bar.com",
                "--password",
                "123",
            ],
        )
        assert res.exit_code == 0
        mocked_login.assert_called_once()
        mocked_download_file.assert_called_once_with(
            "cli_test_data/1/0/bar.txt",
            "https://foo.com/bar.txt",
            True,
            False,
        )
        mocked_sample_details.assert_called_once()
        mocked_qc_metrics.assert_called_once()
        mocked_get_metadata.assert_called_once()


def test_sample_ids_provided_no_qc_file(mocker):
    """Check flow with sample ids and no file present."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        mocked_login = mocker.patch.object(
            APIClient, "login", return_value=None
        )
        mocked_sample_details = mocker.patch.object(
            APIClient,
            "get_sample_details",
            return_value={
                "id": 0,
                "client_id": 1,
                "last_status": {
                    "id": str(uuid4()),
                    "status": "succeeded",
                    "created": "2020-07-28T12:46:22.719862Z",
                },
                "archive_last_status": {
                    "id": str(uuid4()),
                    "status": "available",
                    "created": "2020-07-28T12:46:22.719862Z",
                    "transition_cutoff": "2020-08-28T12:46:22.719862Z",
                },
                "files": [],
            },
        )
        mocked_qc_metrics = mocker.patch.object(
            APIClient,
            "get_sample_qc_metrics",
            return_value={"results": [{"foo": 12}]},
        )
        mocked_get_metadata = mocker.patch.object(
            APIClient,
            "get_metadata",
            return_value={"metadata": [{"foo": 12}]},
        )
        res = runner.invoke(
            download,
            [
                "cli_test_data",
                "--sample-ids",
                "0",
                "--email",
                "foo@bar.com",
                "--password",
                "123",
            ],
        )
        assert res.exit_code == 0
        mocked_login.assert_called_once()
        mocked_sample_details.assert_called_once()
        mocked_qc_metrics.assert_called_once()
        mocked_get_metadata.assert_called_once()


def test_sample_ids_provided_no_metadata_file(mocker):
    """Check flow with sample ids and no metadata present."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        mocked_login = mocker.patch.object(
            APIClient, "login", return_value=None
        )
        mocked_sample_details = mocker.patch.object(
            APIClient,
            "get_sample_details",
            return_value={
                "id": 0,
                "client_id": 1,
                "last_status": {
                    "id": str(uuid4()),
                    "status": "succeeded",
                    "created": "2020-07-28T12:46:22.719862Z",
                },
                "archive_last_status": {
                    "id": str(uuid4()),
                    "status": "available",
                    "created": "2020-07-28T12:46:22.719862Z",
                    "transition_cutoff": "2020-08-28T12:46:22.719862Z",
                },
                "files": [],
            },
        )
        mocked_get_metadata = mocker.patch.object(
            APIClient,
            "get_metadata",
            return_value={"metadata": [{"foo": 12}]},
        )
        mocked_qc_metrics = mocker.patch.object(
            APIClient,
            "get_sample_qc_metrics",
            return_value={"results": [{"foo": 12}]},
        )
        res = runner.invoke(
            download,
            [
                "cli_test_data",
                "--sample-ids",
                "0",
                "--email",
                "foo@bar.com",
                "--password",
                "123",
            ],
        )
        assert res.exit_code == 0
        mocked_login.assert_called_once()
        mocked_sample_details.assert_called_once()
        mocked_get_metadata.assert_called_once()
        mocked_qc_metrics.assert_called_once()


def test_multiple_credentials_not_allowed():
    """Test that in providing multiple credentials is not allowed."""
    runner = CliRunner()
    res = runner.invoke(
        download,
        [
            "some_test_data",
            "--sample-ids",
            "0",
            "--email",
            "foo@bar.com",
            "--password",
            "123",
            "--api-key",
            "foobar",
        ],
    )
    assert res.exit_code == 1
    assert "Please provide either username/password or API key." in res.output


def test_download_stdout_no_flag(mocker):
    """Test command exits if no flag provided and stdout defined."""
    runner = CliRunner()
    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_project_samples = mocker.patch.object(
        APIClient,
        "get_project_samples",
        return_value={"results": [{"id": 0}], "meta": {"next": None}},
    )
    res = runner.invoke(
        download,
        [
            "-",
            "--project-id",
            "123",
            "--email",
            "foo@bar.com",
            "--password",
            "12345",
        ],
    )
    assert res.exit_code == 1
    mocked_login.assert_called_once()
    mocked_project_samples.assert_called_once()
    output_line = io.BytesIO()
    sys.stdout = output_line
    echo("ERROR: Cannot have - as a destination without download-urls.")
    assert output_line.getvalue() in res.output.encode()


def test_download_stdout_with_flag(mocker):
    """Test command outputs json to stdout."""
    runner = CliRunner()
    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_project_samples = mocker.patch.object(
        APIClient,
        "get_project_samples",
        return_value={"results": [{"id": 0}], "meta": {"next": None}},
    )
    last_status_id = str(uuid4())
    archive_last_status_id = str(uuid4())
    file_id = str(uuid4())
    mocked_sample_details = mocker.patch.object(
        APIClient,
        "get_sample_details",
        return_value={
            "id": 0,
            "client_id": 1,
            "last_status": {
                "id": last_status_id,
                "status": "succeeded",
                "created": "2020-07-28T12:46:22.719862Z",
            },
            "archive_last_status": {
                "id": archive_last_status_id,
                "status": "available",
                "created": "2020-07-28T12:46:22.719862Z",
                "transition_cutoff": "2020-08-28T12:46:22.719862Z",
            },
            "files": [
                {
                    "id": file_id,
                    "file_type": "txt",
                    "download_url": "https://foo.com/bar.txt",
                }
            ],
        },
    )
    res = runner.invoke(
        download,
        [
            "-",
            "--project-id",
            "123",
            "--email",
            "foo@bar.com",
            "--password",
            "12345",
            "--download-urls",
        ],
    )
    assert res.exit_code == 0
    mocked_login.assert_called_once()
    mocked_project_samples.assert_called_once()
    mocked_sample_details.assert_called_once()
    output_line = io.BytesIO()
    sys.stdout = output_line
    mocked_result = json.dumps(
        [
            {
                "gencove_id": 0,
                "client_id": 1,
                "last_status": {
                    "id": last_status_id,
                    "status": "succeeded",
                    "created": "2020-07-28T12:46:22.719862Z",
                },
                "archive_last_status": {
                    "id": archive_last_status_id,
                    "status": "available",
                    "created": "2020-07-28T12:46:22.719862Z",
                    "transition_cutoff": "2020-08-28T12:46:22.719862Z",
                },
                "files": {
                    "txt": {
                        "id": file_id,
                        "download_url": "https://foo.com/bar.txt",
                    }
                },
            }
        ],
        indent=4,
    )
    echo(mocked_result)
    assert output_line.getvalue() in res.output.encode()


def test_download_urls_to_file(mocker):
    """Test saving downloaded urls output to a json file."""
    runner = CliRunner()
    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_project_samples = mocker.patch.object(
        APIClient,
        "get_project_samples",
        return_value={"results": [{"id": 0}], "meta": {"next": None}},
    )
    last_status_id = str(uuid4())
    archive_last_status_id = str(uuid4())
    file_id = str(uuid4())
    mocked_sample_details = mocker.patch.object(
        APIClient,
        "get_sample_details",
        return_value={
            "id": 0,
            "client_id": 1,
            "last_status": {
                "id": last_status_id,
                "status": "succeeded",
                "created": "2020-07-28T12:46:22.719862Z",
            },
            "archive_last_status": {
                "id": archive_last_status_id,
                "status": "available",
                "created": "2020-07-28T12:46:22.719862Z",
                "transition_cutoff": "2020-08-28T12:46:22.719862Z",
            },
            "files": [
                {
                    "id": file_id,
                    "file_type": "txt",
                    "download_url": "https://foo.com/bar.txt",
                }
            ],
        },
    )
    mocked_output_list = mocker.patch(
        "gencove.command.download.main.Download.output_list"
    )
    with runner.isolated_filesystem():
        res = runner.invoke(
            download,
            [
                "output.json",
                "--project-id",
                "123",
                "--email",
                "foo@bar.com",
                "--password",
                "12345",
                "--download-urls",
            ],
        )
        assert res.exit_code == 0
        mocked_login.assert_called_once()
        mocked_project_samples.assert_called_once()
        mocked_sample_details.assert_called_once()
        mocked_output_list.assert_called_once()


def test_download_no_progress(mocker):
    """Test command doesn't show progress bar."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        mocked_login = mocker.patch.object(
            APIClient, "login", return_value=None
        )
        mocked_sample_details = mocker.patch.object(
            APIClient,
            "get_sample_details",
            return_value={
                "id": 0,
                "client_id": 1,
                "last_status": {
                    "id": str(uuid4()),
                    "status": "succeeded",
                    "created": "2020-07-28T12:46:22.719862Z",
                },
                "archive_last_status": {
                    "id": str(uuid4()),
                    "status": "available",
                    "created": "2020-07-28T12:46:22.719862Z",
                    "transition_cutoff": "2020-08-28T12:46:22.719862Z",
                },
                "files": [
                    {
                        "id": str(uuid4()),
                        "file_type": "txt",
                        "download_url": "https://foo.com/bar.txt",
                    }
                ],
            },
        )
        mocked_qc_metrics = mocker.patch.object(
            APIClient,
            "get_sample_qc_metrics",
            return_value={"results": [{"foo": 12}]},
        )
        mocked_get_metadata = mocker.patch.object(
            APIClient,
            "get_metadata",
            return_value=dict(
                metadata=None,
            ),
        )
        mocked_download_file = mocker.patch(
            "gencove.command.download.main.download_file"
        )
        res = runner.invoke(
            download,
            [
                "cli_test_data",
                "--sample-ids",
                "0",
                "--email",
                "foo@bar.com",
                "--password",
                "123",
                "--no-progress",
            ],
        )
        assert res.exit_code == 0
        mocked_login.assert_called_once()
        mocked_download_file.assert_called_once_with(
            "cli_test_data/1/0/bar.txt", "https://foo.com/bar.txt", True, True
        )
        mocked_sample_details.assert_called_once()
        mocked_qc_metrics.assert_called_once()
        mocked_get_metadata.assert_called_once()


def test_project_id_provided_skip_existing_qc_and_metadata(mocker):
    """Check happy flow."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        mocked_login = mocker.patch.object(
            APIClient, "login", return_value=None
        )
        mocked_project_samples = mocker.patch.object(
            APIClient,
            "get_project_samples",
            return_value={"results": [{"id": 0}], "meta": {"next": None}},
        )
        mocked_sample_details = mocker.patch.object(
            APIClient,
            "get_sample_details",
            return_value={
                "id": 0,
                "client_id": 1,
                "last_status": {
                    "id": str(uuid4()),
                    "status": "succeeded",
                    "created": "2020-07-28T12:46:22.719862Z",
                },
                "archive_last_status": {
                    "id": str(uuid4()),
                    "status": "available",
                    "created": "2020-07-28T12:46:22.719862Z",
                    "transition_cutoff": "2020-08-28T12:46:22.719862Z",
                },
                "files": [
                    {
                        "id": str(uuid4()),
                        "file_type": "txt",
                        "download_url": "https://foo.com/bar.txt",
                    }
                ],
            },
        )
        mocked_qc_metrics = mocker.patch.object(
            APIClient,
            "get_sample_qc_metrics",
            return_value={"results": [{"foo": 12}]},
        )
        mocked_get_metadata = mocker.patch.object(
            APIClient,
            "get_metadata",
            return_value=dict(
                metadata=None,
            ),
        )
        mocked_download_file = mocker.patch(
            "gencove.command.download.main.download_file"
        )
        res = runner.invoke(
            download,
            [
                "cli_test_data",
                "--project-id",
                "123",
                "--email",
                "foo@bar.com",
                "--password",
                "123",
                "--no-skip-existing",
            ],
        )
        assert res.exit_code == 0
        mocked_login.assert_called_once()
        mocked_project_samples.assert_called_once()
        mocked_qc_metrics.assert_called_once()
        mocked_get_metadata.assert_called_once()
        mocked_download_file.assert_called_once()
        mocked_sample_details.assert_called_once()

        # call it the second time
        mocked_qc_metrics = mocker.patch.object(
            APIClient,
            "get_sample_qc_metrics",
            return_value={"results": [{"foo": 12}]},
        )
        mocked_get_metadata = mocker.patch.object(
            APIClient,
            "get_metadata",
            return_value=dict(
                metadata=None,
            ),
        )
        res = runner.invoke(
            download,
            [
                "cli_test_data",
                "--project-id",
                "123",
                "--email",
                "foo@bar.com",
                "--password",
                "123",
                "--skip-existing",
            ],
        )
        assert res.exit_code == 0
        mocked_qc_metrics.assert_not_called()
        mocked_get_metadata.assert_not_called()


def test_download_not_working_because_archived(mocker):
    """Test command doesn't download archived files."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        mocked_login = mocker.patch.object(
            APIClient, "login", return_value=None
        )
        mocked_sample_details = mocker.patch.object(
            APIClient,
            "get_sample_details",
            return_value={
                "id": 0,
                "client_id": 1,
                "last_status": {
                    "id": str(uuid4()),
                    "status": "succeeded",
                    "created": "2020-07-28T12:46:22.719862Z",
                },
                "archive_last_status": {
                    "id": str(uuid4()),
                    "status": "archived",
                    "created": "2020-07-28T12:46:22.719862Z",
                    "transition_cutoff": "2020-08-28T12:46:22.719862Z",
                },
                "files": [
                    {
                        "id": str(uuid4()),
                        "file_type": "txt",
                        "download_url": None,
                    }
                ],
            },
        )
        mocked_qc_metrics = mocker.patch.object(
            APIClient,
            "get_sample_qc_metrics",
            return_value={"results": [{"foo": 12}]},
        )
        mocked_get_metadata = mocker.patch.object(
            APIClient,
            "get_metadata",
            return_value=dict(
                metadata=None,
            ),
        )
        mocked_download_file = mocker.patch(
            "gencove.command.download.main.download_file"
        )
        res = runner.invoke(
            download,
            [
                "cli_test_data",
                "--sample-ids",
                "0",
                "--email",
                "foo@bar.com",
                "--password",
                "123",
            ],
        )
        assert res.exit_code == 1
        mocked_login.assert_called_once()
        mocked_download_file.assert_not_called()
        mocked_sample_details.assert_called_once()
        mocked_qc_metrics.assert_not_called()
        mocked_get_metadata.assert_not_called()


def test_project_id_provided_filter_not_archived(mocker):
    """Check happy flow."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        mocked_login = mocker.patch.object(
            APIClient, "login", return_value=None
        )
        mocked_project_samples = mocker.patch.object(
            APIClient,
            "get_project_samples",
            return_value={"results": [], "meta": {"next": None}},
        )
        mocked_sample_details = mocker.patch.object(
            APIClient,
            "get_sample_details",
            return_value={
                "id": 0,
                "client_id": 1,
                "last_status": {
                    "id": str(uuid4()),
                    "status": "succeeded",
                    "created": "2020-07-28T12:46:22.719862Z",
                },
                "archive_last_status": {
                    "id": str(uuid4()),
                    "status": "archived",
                    "created": "2020-07-28T12:46:22.719862Z",
                    "transition_cutoff": "2020-08-28T12:46:22.719862Z",
                },
                "files": [
                    {
                        "id": str(uuid4()),
                        "file_type": "txt",
                        "download_url": None,
                    }
                ],
            },
        )
        mocked_qc_metrics = mocker.patch.object(
            APIClient,
            "get_sample_qc_metrics",
            return_value={"results": [{"foo": 12}]},
        )
        mocked_get_metadata = mocker.patch.object(
            APIClient,
            "get_metadata",
            return_value=dict(
                metadata=None,
            ),
        )
        mocked_download_file = mocker.patch(
            "gencove.command.download.main.download_file"
        )
        res = runner.invoke(
            download,
            [
                "cli_test_data",
                "--project-id",
                "123",
                "--email",
                "foo@bar.com",
                "--password",
                "123",
            ],
        )
        assert res.exit_code == 1
        mocked_login.assert_called_once()
        mocked_project_samples.assert_called_once()
        mocked_qc_metrics.assert_not_called()
        mocked_get_metadata.assert_not_called()
        mocked_download_file.assert_not_called()
        mocked_sample_details.assert_not_called()
