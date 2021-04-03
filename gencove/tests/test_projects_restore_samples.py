"""Test project's restore samples command."""

from uuid import uuid4

from click.testing import CliRunner

from gencove.client import (
    APIClient,
    APIClientError,
)  # noqa: I100
from gencove.command.projects.cli import restore_project_samples


def test_restore_project_samples__bad_project_id(mocker):
    """Test restore project samples when non-uuid string is used as project
    id."""
    runner = CliRunner()
    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_restore_project_samples = mocker.patch.object(
        APIClient,
        "restore_project_samples",
    )
    res = runner.invoke(
        restore_project_samples,
        [
            "1111111",
            "--email",
            "foo@bar.com",
            "--password",
            "123",
            "--sample-ids",
            "11111111-1111-1111-1111-111111111111,22222222-2222-2222-2222-222222222222",  # noqa
        ],
    )
    assert res.exit_code == 1
    mocked_login.assert_called_once()
    mocked_restore_project_samples.assert_not_called()
    assert "Project ID is not valid" in res.output


def test_restore_project_samples__not_owned_project(mocker):
    """Test restore project samples failure when project is not owned."""
    mocked_response = {"detail": "Not found."}

    runner = CliRunner()
    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_restore_project_samples = mocker.patch.object(
        APIClient, "restore_project_samples", return_value=mocked_response
    )

    mocked_restore_project_samples = mocker.patch.object(
        APIClient,
        "restore_project_samples",
        side_effect=APIClientError(message="", status_code=404),
    )

    res = runner.invoke(
        restore_project_samples,
        [
            str(uuid4()),
            "--email",
            "foo@bar.com",
            "--password",
            "123",
            "--sample-ids",
            "11111111-1111-1111-1111-111111111111,22222222-2222-2222-2222-222222222222",  # noqa
        ],
    )
    assert res.exit_code == 0
    mocked_login.assert_called_once()
    mocked_restore_project_samples.assert_called_once()
    assert "you do not have permission required" in res.output


def test_restore_project_samples__success__empty_sample_ids(mocker):
    """Test restore project samples success when an empty list of sample ids
    is sent."""
    runner = CliRunner()
    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_restore_project_samples = mocker.patch.object(
        APIClient, "restore_project_samples", return_value=""
    )

    mocked_restore_project_samples = mocker.patch.object(
        APIClient,
        "restore_project_samples",
        side_effect=APIClientError(message="", status_code=400),
    )

    res = runner.invoke(
        restore_project_samples,
        [
            str(uuid4()),
            "--email",
            "foo@bar.com",
            "--password",
            "123",
            "--sample-ids",
            "",
        ],
    )
    assert res.exit_code == 0
    mocked_login.assert_called_once()
    mocked_restore_project_samples.assert_called_once()


def test_restore_project_samples__invalid_sample_ids(mocker):
    """Test restore project samples failure when an empty list of sample ids
    is sent."""
    mocked_response = {"sample_ids": ["This list may not be empty."]}

    runner = CliRunner()
    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_restore_project_samples = mocker.patch.object(
        APIClient, "restore_project_samples", return_value=mocked_response
    )

    mocked_restore_project_samples = mocker.patch.object(
        APIClient,
        "restore_project_samples",
        side_effect=APIClientError(message="", status_code=400),
    )

    res = runner.invoke(
        restore_project_samples,
        [
            str(uuid4()),
            "--email",
            "foo@bar.com",
            "--password",
            "123",
            "--sample-ids",
            "1111,222",
        ],
    )
    assert res.exit_code == 1
    mocked_login.assert_called_once()
    mocked_restore_project_samples.assert_not_called()
    assert "Not all sample IDs are valid" in res.output


def test_restore_project_samples__sample_not_in_project(mocker):
    """Test restore project samples with sample not in project."""
    mocked_response = {
        "sample_ids": [
            "All sample ids must be part of the current project and "
            "in archived status."
        ]
    }

    runner = CliRunner()
    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_restore_project_samples = mocker.patch.object(
        APIClient, "restore_project_samples", return_value=mocked_response
    )
    mocked_restore_project_samples = mocker.patch.object(
        APIClient,
        "restore_project_samples",
        side_effect=APIClientError(message="", status_code=400),
    )

    res = runner.invoke(
        restore_project_samples,
        [
            str(uuid4()),
            "--email",
            "foo@bar.com",
            "--password",
            "123",
            "--sample-ids",
            "11111111-1111-1111-1111-111111111111",
        ],
    )
    assert res.exit_code == 0
    mocked_login.assert_called_once()
    mocked_restore_project_samples.assert_called_once()
    assert (
        "There was an error requesting project samples restore" in res.output
    )


def test_restore_project_samples__success(mocker):
    """Test restore project samples success."""
    runner = CliRunner()
    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_restore_project_samples = mocker.patch.object(
        APIClient, "restore_project_samples", return_value=None
    )

    res = runner.invoke(
        restore_project_samples,
        [
            str(uuid4()),
            "--email",
            "foo@bar.com",
            "--password",
            "123",
            "--sample-ids",
            "11111111-1111-1111-1111-111111111111,22222222-2222-2222-2222-222222222222",  # noqa
        ],
    )
    assert res.exit_code == 0
    mocked_login.assert_called_once()
    mocked_restore_project_samples.assert_called_once()
    assert "Request to restore samples accepted" in res.output
