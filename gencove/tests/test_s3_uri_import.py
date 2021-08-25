"""Test S3's projects import command."""

from uuid import uuid4

from click.testing import CliRunner

from gencove.client import (
    APIClient,
    APIClientError,
)
from gencove.command.s3_imports.s3_import.cli import s3_import


def test_s3_import__bad_project_id(mocker):
    """Test S3 import when non-uuid string is used as project
    id."""
    runner = CliRunner()
    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_import_s3_projects = mocker.patch.object(
        APIClient,
        "s3_uri_import",
    )
    res = runner.invoke(
        s3_import,
        [
            "s3://bucket/path/",
            "s3://bucket/path/",
            "--email",
            "foo@bar.com",
            "--password",
            "123",
        ],
    )
    assert res.exit_code == 1
    mocked_login.assert_called_once()
    mocked_import_s3_projects.assert_not_called()
    assert "Project ID is not valid" in res.output


def test_s3_import__bad_json(mocker):
    """Test S3 import when bad JSON is used."""
    runner = CliRunner()
    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_import_s3_projects = mocker.patch.object(
        APIClient,
        "s3_uri_import",
    )
    res = runner.invoke(
        s3_import,
        [
            "s3://bucket/path/",
            str(uuid4()),
            "--metadata-json",
            "{bad:",
            "--email",
            "foo@bar.com",
            "--password",
            "123",
        ],
    )
    assert res.exit_code == 1
    mocked_login.assert_called_once()
    mocked_import_s3_projects.assert_not_called()
    assert "Metadata JSON is not valid" in res.output


# the following test will work for any 400 case:
# (too many projects, no projects (cannot happen), parse error
# no samples in the projects or too many samples)
def test_s3_import__no_pipeline_capabilities(mocker):
    """Test S3 import failure when project has no
    pipeline capabilities.
    """
    runner = CliRunner()
    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_import_s3_projects = mocker.patch.object(
        APIClient,
        "s3_uri_import",
        side_effect=APIClientError(
            message="Project configuration must be set before adding "
            "samples to a project.",
            status_code=400,
        ),
    )

    res = runner.invoke(
        s3_import,
        [
            "s3://bucket/path/",
            str(uuid4()),
            "--email",
            "foo@bar.com",
            "--password",
            "123",
        ],
    )
    assert res.exit_code == 1
    mocked_login.assert_called_once()
    mocked_import_s3_projects.assert_called_once()
    assert "There was an error importing from S3." in res.output
    assert (
        "Project configuration must be set before adding samples to a project."
        in res.output
    )


def test_s3_import__not_owned_project(mocker):
    """Test S3 import failure when project is not owned."""
    runner = CliRunner()
    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_import_s3_projects = mocker.patch.object(
        APIClient,
        "s3_uri_import",
        side_effect=APIClientError(message="", status_code=403),
    )

    res = runner.invoke(
        s3_import,
        [
            "s3://bucket/path/",
            str(uuid4()),
            "--email",
            "foo@bar.com",
            "--password",
            "123",
        ],
    )
    assert res.exit_code == 1
    mocked_login.assert_called_once()
    mocked_import_s3_projects.assert_called_once()
    assert "You do not have the sufficient permission" in res.output


def test_s3_import__success_with_json(mocker):
    """Test S3 import success with optional json passed."""
    runner = CliRunner()
    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_import_s3_projects = mocker.patch.object(
        APIClient,
        "s3_uri_import",
        return_value=None,
    )

    res = runner.invoke(
        s3_import,
        [
            "s3://bucket/path/",
            str(uuid4()),
            "--metadata-json",
            '{"somekey": "somevalue"}',
            "--email",
            "foo@bar.com",
            "--password",
            "123",
        ],
    )
    assert res.exit_code == 0
    mocked_login.assert_called_once()
    mocked_import_s3_projects.assert_called_once()
    assert "Request to import samples from S3 accepted." in res.output


def test_s3_import__success(mocker):
    """Test S3 import success."""
    runner = CliRunner()
    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_import_s3_projects = mocker.patch.object(
        APIClient,
        "s3_uri_import",
        return_value=None,
    )

    res = runner.invoke(
        s3_import,
        [
            "s3://bucket/path/",
            str(uuid4()),
            "--email",
            "foo@bar.com",
            "--password",
            "123",
        ],
    )
    assert res.exit_code == 0
    mocked_login.assert_called_once()
    mocked_import_s3_projects.assert_called_once()
    assert "Request to import samples from S3 accepted." in res.output
