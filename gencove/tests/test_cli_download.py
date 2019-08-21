"""Test download command."""
from click.testing import CliRunner

from gencove.cli import download
from gencove.client import APIClient


def test_no_required_options():
    """Test that command exits without project id or sample id provided."""
    runner = CliRunner()
    res = runner.invoke(download, ["cli_test_data"])
    assert res.exit_code == 0


def test_both_project_id_and_sample_ids_provided():
    """Command exits if both project id and sample ids are provided."""
    runner = CliRunner()
    res = runner.invoke(
        download,
        ["cli_test_data", "--project-id", "123", "--sample-ids", "1,2,3"],
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
        mocked_download_file = mocker.patch(
            "gencove.command.download._download_file"
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
        mocked_download_file.assert_called_once()
        mocked_sample_details.assert_called_once()
