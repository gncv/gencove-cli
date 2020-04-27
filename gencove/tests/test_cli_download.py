"""Test download command."""
import os

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
        assert res.exit_code == 0


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
    assert res.exit_code == 0


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
                "last_status": {"status": "succeeded"},
                "files": [
                    {
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
        mocked_download_file = mocker.patch(
            "gencove.command.download.main.download_file"
        )
        mocked_save_qc_metrics = mocker.patch(
            "gencove.command.download.main.save_qc_file"
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
        mocked_download_file.assert_called_once()
        mocked_save_qc_metrics.assert_called_once()
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
                "last_status": {"status": "succeeded"},
                "files": [
                    {
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
        mocked_download_file = mocker.patch(
            "gencove.command.download.main.download_file"
        )
        mocked_save_qc_metrics = mocker.patch(
            "gencove.command.download.main.save_qc_file"
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
        mocked_download_file.assert_called_once()
        mocked_sample_details.assert_called_once()
        mocked_qc_metrics.assert_called_once()
        mocked_save_qc_metrics.assert_called_once()


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
    assert res.exit_code == 0
    assert "Please provide either username/password or API key." in res.output
