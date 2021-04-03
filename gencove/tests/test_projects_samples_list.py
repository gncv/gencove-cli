"""Test project list samples command."""
import io
import sys
from datetime import datetime, timedelta
from uuid import uuid4

from click.testing import CliRunner

from gencove.client import APIClient, APIClientError, APIClientTimeout
from gencove.command.projects.cli import list_project_samples
from gencove.logger import echo_data


def test_list_empty(mocker):
    """Test project has no samples."""
    runner = CliRunner()
    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_get_project_samples = mocker.patch.object(
        APIClient,
        "get_project_samples",
        return_value=dict(results=[], meta=dict(next=None)),
    )
    res = runner.invoke(
        list_project_samples,
        [str(uuid4()), "--email", "foo@bar.com", "--password", "123"],
    )
    assert res.exit_code == 0
    mocked_login.assert_called_once()
    mocked_get_project_samples.assert_called_once()
    assert res.output == ""


def test_list_projects_bad_project_id(mocker):
    """Test project samples throw an error if project id is not uuid."""
    runner = CliRunner()
    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)

    project_id = "123456"

    res = runner.invoke(
        list_project_samples,
        [project_id, "--email", "foo@bar.com", "--password", "123"],
    )
    assert res.exit_code == 1
    mocked_login.assert_called_once()
    output_line = io.BytesIO()
    sys.stdout = output_line
    echo_data(
        "\n".join(
            [
                "ERROR: Project ID is not valid. Exiting.",
                "Aborted!",
            ]
        )
    )
    assert output_line.getvalue() == res.output.encode()


def test_list_projects_no_project(mocker):
    """Test project samples throw an error if no project available."""
    runner = CliRunner()
    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_get_project_samples = mocker.patch.object(
        APIClient,
        "get_project_samples",
        side_effect=APIClientError(
            message="API Client Error: Not Found: Not found.", status_code=404
        ),
        return_value={"detail": "Not found"},
    )

    project_id = str(uuid4())

    res = runner.invoke(
        list_project_samples,
        [project_id, "--email", "foo@bar.com", "--password", "123"],
    )
    assert res.exit_code == 1
    mocked_login.assert_called_once()
    mocked_get_project_samples.assert_called_once()

    output_line = io.BytesIO()
    sys.stdout = output_line
    echo_data(
        "\n".join(
            [
                "ERROR: Project {} does not exist or you do not have"
                " permission required to access it.".format(project_id),
                "ERROR: API Client Error: Not Found: Not found.",
                "Aborted!",
            ]
        )
    )
    assert output_line.getvalue() == res.output.encode()


def test_list_project_samples_slow_response_retry(mocker):
    """Test project samples slow response retry."""
    runner = CliRunner()
    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_get_project_samples = mocker.patch.object(
        APIClient,
        "get_project_samples",
        side_effect=APIClientTimeout("Could not connect to the api server"),
    )

    res = runner.invoke(
        list_project_samples,
        [str(uuid4()), "--email", "foo@bar.com", "--password", "123"],
    )
    assert res.exit_code == 1
    mocked_login.assert_called_once()
    assert mocked_get_project_samples.call_count == 2


def test_list_project_samples(mocker):
    """Test project samples being outputed to the shell."""
    mocked_samples = dict(
        meta=dict(count=1, next=None),
        results=[
            {
                "id": str(uuid4()),
                "client_id": "tester client id",
                "last_status": {
                    "created": (
                        datetime.utcnow() - timedelta(days=3)
                    ).isoformat(),
                    "status": "succeeded",
                },
                "archive_last_status": {
                    "status": "available",
                    "created": (
                        datetime.utcnow() - timedelta(days=1)
                    ).isoformat(),
                    "transition_cutoff": (
                        datetime.utcnow() + timedelta(days=6)
                    ).isoformat(),
                },
            }
        ],
    )
    runner = CliRunner()
    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_get_project_samples = mocker.patch.object(
        APIClient, "get_project_samples", return_value=mocked_samples
    )

    res = runner.invoke(
        list_project_samples,
        [str(uuid4()), "--email", "foo@bar.com", "--password", "123"],
    )
    assert res.exit_code == 0
    mocked_login.assert_called_once()
    mocked_get_project_samples.assert_called_once()

    output_line = io.BytesIO()
    sys.stdout = output_line
    echo_data(
        "\t".join(
            [
                mocked_samples["results"][0]["last_status"]["created"],
                mocked_samples["results"][0]["id"],
                mocked_samples["results"][0]["client_id"],
                mocked_samples["results"][0]["last_status"]["status"],
                mocked_samples["results"][0]["archive_last_status"]["status"],
            ]
        )
    )
    assert output_line.getvalue() == res.output.encode()
