"""Test project list command."""
# pylint: disable=wrong-import-order
import io
import sys
from datetime import datetime, timedelta
from uuid import uuid4

from click import echo
from click.testing import CliRunner

from gencove.client import APIClient  # noqa: I100
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
    print(res.output)
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
