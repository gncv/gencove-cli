"""Test project's batches list command."""

import io
import sys
from uuid import uuid4

from click import echo
from click.testing import CliRunner

from gencove.client import APIClient, APIClientTimeout  # noqa: I100
from gencove.command.projects.cli import list_project_batches


def test_list_project_batches__empty(mocker):
    """Test project has not batches."""
    runner = CliRunner()
    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_get_project_batches = mocker.patch.object(
        APIClient,
        "get_project_batches",
        return_value=dict(results=[], meta=dict(next=None)),
    )
    res = runner.invoke(
        list_project_batches,
        [str(uuid4()), "--email", "foo@bar.com", "--password", "123"],
    )
    assert res.exit_code == 0
    mocked_login.assert_called_once()
    mocked_get_project_batches.assert_called_once()
    assert res.output == ""


MOCKED_BATCHES = dict(
    meta=dict(count=2, next=None),
    results=[
        {
            "id": str(uuid4()),
            "name": "foo",
            "batch_type": "hd777k",
            "files": [
                {
                    "id": str(uuid4()),
                    "file_type": "report-zip",
                    "download_url": "https://foo.com/bar.zip",
                }
            ],
            "last_status": {
                "created": "2020-07-27T12:46:22.719862Z",
                "id": str(uuid4()),
                "status": "succeeded",
            },
        },
        {
            "id": str(uuid4()),
            "name": "bar",
            "batch_type": "hd777k",
            "files": [
                {
                    "id": str(uuid4()),
                    "file_type": "report-zip",
                    "download_url": "https://baz.com/bar.zip",
                }
            ],
            "last_status": {
                "created": "2020-07-28T12:46:22.719862Z",
                "id": str(uuid4()),
                "status": "running",
            },
        },
    ],
)


def test_list_project_batches__not_empty(mocker):
    """Test project batches being outputed to the shell."""
    runner = CliRunner()
    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_get_project_batches = mocker.patch.object(
        APIClient, "get_project_batches", return_value=MOCKED_BATCHES
    )

    res = runner.invoke(
        list_project_batches,
        [str(uuid4()), "--email", "foo@bar.com", "--password", "123"],
    )
    assert res.exit_code == 0
    mocked_login.assert_called_once()
    mocked_get_project_batches.assert_called_once()

    output_line = io.BytesIO()
    sys.stdout = output_line
    line_one = "\t".join(
        [
            MOCKED_BATCHES["results"][0]["id"],
            MOCKED_BATCHES["results"][0]["last_status"]["created"],
            MOCKED_BATCHES["results"][0]["last_status"]["status"],
            MOCKED_BATCHES["results"][0]["batch_type"],
            MOCKED_BATCHES["results"][0]["name"],
        ]
    )
    line_two = "\t".join(
        [
            MOCKED_BATCHES["results"][1]["id"],
            MOCKED_BATCHES["results"][1]["last_status"]["created"],
            MOCKED_BATCHES["results"][1]["last_status"]["status"],
            MOCKED_BATCHES["results"][1]["batch_type"],
            MOCKED_BATCHES["results"][1]["name"],
        ]
    )
    echo("\n".join([line_one, line_two]))
    assert output_line.getvalue() == res.output.encode()


def test_list_project_batches__not_empty_slow_response_retry(mocker):
    """Test project batches slow response retry."""
    runner = CliRunner()
    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_get_project_batches = mocker.patch.object(
        APIClient,
        "get_project_batches",
        side_effect=APIClientTimeout("Could not connect to the api server"),
    )

    res = runner.invoke(
        list_project_batches,
        [str(uuid4()), "--email", "foo@bar.com", "--password", "123"],
    )
    assert res.exit_code == 1
    mocked_login.assert_called_once()
    assert mocked_get_project_batches.call_count == 2
