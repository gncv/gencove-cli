"""Test project list samples command."""
import io
import sys
from datetime import datetime, timedelta
from uuid import uuid4

from click.testing import CliRunner

from gencove.client import APIClient  # noqa: I100
from gencove.command.projects.cli import list_project_samples
from gencove.logger import echo


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


MOCKED_SAMPLES = dict(
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
        }
    ],
)


def test_list_projects(mocker):
    """Test project samples being outputed to the shell."""
    runner = CliRunner()
    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_get_project_samples = mocker.patch.object(
        APIClient, "get_project_samples", return_value=MOCKED_SAMPLES
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
    echo(
        "\t".join(
            [
                MOCKED_SAMPLES["results"][0]["last_status"]["created"],
                MOCKED_SAMPLES["results"][0]["id"],
                MOCKED_SAMPLES["results"][0]["client_id"],
                MOCKED_SAMPLES["results"][0]["last_status"]["status"],
            ]
        )
    )
    assert output_line.getvalue() == res.output.encode()
