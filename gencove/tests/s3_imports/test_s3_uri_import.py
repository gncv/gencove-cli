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
    mocked_login.assert_not_called()
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


def test_s3_import__success_with_input_format_fastq(mocker):
    """Test S3 import success with input format fastq."""
    runner = CliRunner()
    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_import_s3_projects = mocker.patch.object(
        APIClient,
        "s3_uri_import",
        return_value=None,
    )

    project_id = str(uuid4())
    res = runner.invoke(
        s3_import,
        [
            "s3://bucket/path/",
            project_id,
            "--input-format",
            "fastq",
            "--email",
            "foo@bar.com",
            "--password",
            "123",
        ],
    )
    assert res.exit_code == 0
    mocked_login.assert_called_once()
    mocked_import_s3_projects.assert_called_once()
    mocked_import_s3_projects.assert_called_with(
        s3_uri="s3://bucket/path/",
        project_id=project_id,
        metadata=None,
        input_format="fastq",
    )
    assert "Request to import samples from S3 accepted." in res.output


def test_s3_import__success_with_input_format_cram(mocker):
    """Test S3 import success with input format cram."""
    runner = CliRunner()
    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_import_s3_projects = mocker.patch.object(
        APIClient,
        "s3_uri_import",
        return_value=None,
    )

    project_id = str(uuid4())
    res = runner.invoke(
        s3_import,
        [
            "s3://bucket/path/",
            project_id,
            "--input-format",
            "cram",
            "--email",
            "foo@bar.com",
            "--password",
            "123",
        ],
    )
    assert res.exit_code == 0
    mocked_login.assert_called_once()
    mocked_import_s3_projects.assert_called_once()
    mocked_import_s3_projects.assert_called_with(
        s3_uri="s3://bucket/path/",
        project_id=project_id,
        metadata=None,
        input_format="cram",
    )
    assert "Request to import samples from S3 accepted." in res.output


def test_s3_import__success_with_input_format_autodetect(mocker):
    """Test S3 import success with input format autodetect (default)."""
    runner = CliRunner()
    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_import_s3_projects = mocker.patch.object(
        APIClient,
        "s3_uri_import",
        return_value=None,
    )

    project_id = str(uuid4())
    res = runner.invoke(
        s3_import,
        [
            "s3://bucket/path/",
            project_id,
            "--input-format",
            "autodetect",
            "--email",
            "foo@bar.com",
            "--password",
            "123",
        ],
    )
    assert res.exit_code == 0
    mocked_login.assert_called_once()
    mocked_import_s3_projects.assert_called_once()
    mocked_import_s3_projects.assert_called_with(
        s3_uri="s3://bucket/path/",
        project_id=project_id,
        metadata=None,
        input_format="autodetect",
    )
    assert "Request to import samples from S3 accepted." in res.output


def test_s3_import__success_with_input_format_and_metadata(mocker):
    """Test S3 import success with both input format and metadata."""
    runner = CliRunner()
    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_import_s3_projects = mocker.patch.object(
        APIClient,
        "s3_uri_import",
        return_value=None,
    )

    project_id = str(uuid4())
    res = runner.invoke(
        s3_import,
        [
            "s3://bucket/path/",
            project_id,
            "--input-format",
            "fastq",
            "--metadata-json",
            '{"batch": "batch1"}',
            "--email",
            "foo@bar.com",
            "--password",
            "123",
        ],
    )
    assert res.exit_code == 0
    mocked_login.assert_called_once()
    mocked_import_s3_projects.assert_called_once()
    mocked_import_s3_projects.assert_called_with(
        s3_uri="s3://bucket/path/",
        project_id=project_id,
        metadata={"batch": "batch1"},
        input_format="fastq",
    )
    assert "Request to import samples from S3 accepted." in res.output


def test_s3_import__invalid_input_format(mocker):
    """Test S3 import failure with invalid input format."""
    runner = CliRunner()
    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_import_s3_projects = mocker.patch.object(
        APIClient,
        "s3_uri_import",
    )

    project_id = str(uuid4())
    res = runner.invoke(
        s3_import,
        [
            "s3://bucket/path/",
            project_id,
            "--input-format",
            "invalid_format",
            "--email",
            "foo@bar.com",
            "--password",
            "123",
        ],
    )
    assert res.exit_code == 2  # Click validation error exit code
    mocked_login.assert_not_called()
    mocked_import_s3_projects.assert_not_called()
    assert "Invalid value for '--input-format'" in res.output
    assert "invalid_format" in res.output
    assert "Choose from:" in res.output or "is not one of" in res.output
