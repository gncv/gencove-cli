"""Test project list command."""
# pylint: disable=wrong-import-order
import io
import sys
from datetime import datetime, timedelta
from uuid import uuid4

from click import echo
from click.testing import CliRunner

from gencove.client import (
    APIClient,
    APIClientError,
    APIClientTimeout,
)  # noqa: I100
from gencove.command.projects.cli import list_projects
from gencove.command.projects.list.constants import (
    PipelineCapabilities,
    Project,
)


def test_list_empty(mocker):
    """Test user organization has no projects."""
    runner = CliRunner()
    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_get_projects = mocker.patch.object(
        APIClient,
        "list_projects",
        return_value=dict(results=[], meta=dict(next=None)),
    )
    res = runner.invoke(
        list_projects, ["--email", "foo@bar.com", "--password", "123"]
    )
    assert res.exit_code == 0
    mocked_login.assert_called_once()
    mocked_get_projects.assert_called_once()
    assert "" in res.output


MOCKED_PROJECTS = dict(
    meta=dict(next=None),
    results=[
        {
            "id": str(uuid4()),
            "name": "test\tproject",
            "description": "",
            "created": (datetime.utcnow() - timedelta(days=7)).isoformat(),
            "organization": str(uuid4()),
            "webhook_url": None,
            "sample_count": 1,
            "pipeline_capabilities": str(uuid4()),
        }
    ],
)

MOCKED_PIPELINE_CAPABILITY = {
    "id": MOCKED_PROJECTS["results"][0]["pipeline_capabilities"],
    "name": "test capability",
    "private": False,
    "merge_vcfs_enabled": False,
}


def test_list_projects_no_permission(mocker):
    """Test projects no permission available to show them."""
    runner = CliRunner()
    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_get_projects = mocker.patch.object(
        APIClient,
        "list_projects",
        side_effect=APIClientError(
            message="API Client Error: Not Found: Not found.", status_code=404
        ),
        return_value={"detail": "Not found"},
    )
    mocked_get_pipeline_capabilities = mocker.patch.object(
        APIClient,
        "get_pipeline_capabilities",
        return_value=MOCKED_PIPELINE_CAPABILITY,
    )
    res = runner.invoke(
        list_projects, ["--email", "foo@bar.com", "--password", "123"]
    )
    assert res.exit_code == 1
    mocked_login.assert_called_once()
    mocked_get_projects.assert_called_once()
    mocked_get_pipeline_capabilities.assert_not_called()

    output_line = io.BytesIO()
    sys.stdout = output_line
    echo(
        "\n".join(
            [
                "ERROR: You do not have permission required to access "
                "the project list.",
                "ERROR: API Client Error: Not Found: Not found.",
                "Aborted!",
            ]
        )
    )
    assert output_line.getvalue() == res.output.encode()


def test_list_projects_slow_response_retry_list(mocker):
    """Test projects slow response retry on the list."""
    runner = CliRunner()
    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_get_projects = mocker.patch.object(
        APIClient,
        "list_projects",
        side_effect=APIClientTimeout("Could not connect to the api server"),
    )
    mocked_get_pipeline_capabilities = mocker.patch.object(
        APIClient,
        "get_pipeline_capabilities",
        side_effect=APIClientTimeout("Could not connect to the api server"),
    )
    res = runner.invoke(
        list_projects, ["--email", "foo@bar.com", "--password", "123"]
    )
    assert res.exit_code == 1
    mocked_login.assert_called_once()
    assert mocked_get_projects.call_count == 2
    mocked_get_pipeline_capabilities.assert_not_called()


def test_list_projects_slow_response_retry_pipeline(mocker):
    """Test projects slow repsonse retry on the pipeline capabilities."""
    runner = CliRunner()
    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_get_projects = mocker.patch.object(
        APIClient, "list_projects", return_value=MOCKED_PROJECTS
    )
    mocked_get_pipeline_capabilities = mocker.patch.object(
        APIClient,
        "get_pipeline_capabilities",
        side_effect=APIClientTimeout("Could not connect to the api server"),
    )
    res = runner.invoke(
        list_projects, ["--email", "foo@bar.com", "--password", "123"]
    )
    assert res.exit_code == 1
    mocked_login.assert_called_once()
    mocked_get_projects.assert_called_once()
    assert mocked_get_pipeline_capabilities.call_count == 3


def test_list_projects(mocker):
    """Test projects being outputed to the shell."""
    runner = CliRunner()
    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_get_projects = mocker.patch.object(
        APIClient, "list_projects", return_value=MOCKED_PROJECTS
    )
    mocked_get_pipeline_capabilities = mocker.patch.object(
        APIClient,
        "get_pipeline_capabilities",
        return_value=MOCKED_PIPELINE_CAPABILITY,
    )
    res = runner.invoke(
        list_projects, ["--email", "foo@bar.com", "--password", "123"]
    )
    assert res.exit_code == 0
    mocked_login.assert_called_once()
    mocked_get_projects.assert_called_once()
    mocked_get_pipeline_capabilities.assert_called_once()

    project = Project(**MOCKED_PROJECTS["results"][0])
    pipeline = PipelineCapabilities(**MOCKED_PIPELINE_CAPABILITY)

    output_line = io.BytesIO()
    sys.stdout = output_line
    echo(
        "\t".join(
            [
                project.created,
                project.id,
                project.name.replace("\t", " "),
                pipeline.name,
            ]
        )
    )
    assert output_line.getvalue() == res.output.encode()
