"""Test BaseSpace's projects import command."""

from uuid import uuid4

from click.testing import CliRunner

from gencove.client import (
    APIClient,
    APIClientError,
)
from gencove.command.basespace.projects.cli import basespace_import


def test_basespace_import__bad_project_id(mocker):
    """Test BaseSpace import when non-uuid string is used as project
    id."""
    runner = CliRunner()
    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_import_basespace_projects = mocker.patch.object(
        APIClient,
        "import_basespace_projects",
    )
    res = runner.invoke(
        basespace_import,
        [
            "1111111",
            "1111111",
            "--email",
            "foo@bar.com",
            "--password",
            "123",
        ],
    )
    assert res.exit_code == 1
    mocked_login.assert_called_once()
    mocked_import_basespace_projects.assert_not_called()
    assert "Project ID is not valid" in res.output


def test_basespace_import__bad_json(mocker):
    """Test BaseSpace import when bad JSON is used."""
    runner = CliRunner()
    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_import_basespace_projects = mocker.patch.object(
        APIClient,
        "import_basespace_projects",
    )
    res = runner.invoke(
        basespace_import,
        [
            "1111111",
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
    mocked_import_basespace_projects.assert_not_called()
    assert "Metadata JSON is not valid" in res.output


# the following test will work for any 400 case:
# (too many projects, no projects (cannot happen), parse error
# no samples in the projects or too many samples)
def test_basespace_import__no_pipeline_capabilities(mocker):
    """Test BaseSpace import failure when project has no
    pipeline capabilities.
    """
    runner = CliRunner()
    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_import_basespace_projects = mocker.patch.object(
        APIClient,
        "import_basespace_projects",
        side_effect=APIClientError(
            message="Project configuration must be set before adding "
            "samples to a project.",
            status_code=400,
        ),
    )

    res = runner.invoke(
        basespace_import,
        [
            "1111111",
            str(uuid4()),
            "--email",
            "foo@bar.com",
            "--password",
            "123",
        ],
    )
    assert res.exit_code == 1
    mocked_login.assert_called_once()
    mocked_import_basespace_projects.assert_called_once()
    assert "There was an error importing Biosamples from BaseSpace." in res.output
    assert (
        "Project configuration must be set before adding samples to a project."
        in res.output
    )


def test_basespace_import__not_owned_project(mocker):
    """Test BaseSpace import failure when project is not owned."""
    runner = CliRunner()
    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_import_basespace_projects = mocker.patch.object(
        APIClient,
        "import_basespace_projects",
        side_effect=APIClientError(message="", status_code=403),
    )

    res = runner.invoke(
        basespace_import,
        [
            "1111111",
            str(uuid4()),
            "--email",
            "foo@bar.com",
            "--password",
            "123",
        ],
    )
    assert res.exit_code == 1
    mocked_login.assert_called_once()
    mocked_import_basespace_projects.assert_called_once()
    assert "You do not have the sufficient permission" in res.output


def test_basespace_import__success_with_json(mocker):
    """Test BaseSpace import success with optional json passed."""
    runner = CliRunner()
    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_import_basespace_projects = mocker.patch.object(
        APIClient,
        "import_basespace_projects",
        return_value=None,
    )

    res = runner.invoke(
        basespace_import,
        [
            "1111111",
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
    mocked_import_basespace_projects.assert_called_once()
    assert "Request to import BaseSpace projects accepted." in res.output


def test_basespace_import__success_with_multiple(mocker):
    """Test BaseSpace import success with multiple BaseSpace projects."""
    runner = CliRunner()
    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_import_basespace_projects = mocker.patch.object(
        APIClient,
        "import_basespace_projects",
        return_value=None,
    )

    res = runner.invoke(
        basespace_import,
        [
            "1111111,2222222",
            str(uuid4()),
            "--email",
            "foo@bar.com",
            "--password",
            "123",
        ],
    )
    assert res.exit_code == 0
    mocked_login.assert_called_once()
    mocked_import_basespace_projects.assert_called_once()
    assert "Request to import BaseSpace projects accepted." in res.output


def test_basespace_import__success(mocker):
    """Test BaseSpace import success."""
    runner = CliRunner()
    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_import_basespace_projects = mocker.patch.object(
        APIClient,
        "import_basespace_projects",
        return_value=None,
    )

    res = runner.invoke(
        basespace_import,
        [
            "1111111",
            str(uuid4()),
            "--email",
            "foo@bar.com",
            "--password",
            "123",
        ],
    )
    assert res.exit_code == 0
    mocked_login.assert_called_once()
    mocked_import_basespace_projects.assert_called_once()
    assert "Request to import BaseSpace projects accepted." in res.output
