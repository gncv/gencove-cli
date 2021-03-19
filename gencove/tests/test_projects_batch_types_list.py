"""Test project's batch types list command."""

import io
import sys
from uuid import uuid4

from click import echo
from click.testing import CliRunner

from gencove.client import APIClient, APIClientTimeout  # noqa: I100
from gencove.command.projects.cli import list_project_batch_types


def test_list_project_batch_types__empty(mocker):
    """Test project has not batch types."""
    runner = CliRunner()
    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_get_project_batch_types = mocker.patch.object(
        APIClient,
        "get_project_batch_types",
        return_value=dict(results=[], meta=dict(next=None)),
    )
    res = runner.invoke(
        list_project_batch_types,
        [str(uuid4()), "--email", "foo@bar.com", "--password", "123"],
    )
    assert res.exit_code == 0
    mocked_login.assert_called_once()
    mocked_get_project_batch_types.assert_called_once()
    assert res.output == ""


MOCKED_BATCH_TYPES = dict(
    meta=dict(count=2, next=None),
    results=[
        {
            "key": "hd777k",
            "description": "foo",
        },
        {
            "key": "illuminahd",
            "description": "bar",
        },
    ],
)


def test_list_project_batch_types__not_empty_slow_response_retry(mocker):
    """Test project batch types being outputed to the shell."""
    runner = CliRunner()
    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_get_project_batch_types = mocker.patch.object(
        APIClient,
        "get_project_batch_types",
        side_effect=APIClientTimeout("Could not connect to the api server"),
    )

    res = runner.invoke(
        list_project_batch_types,
        [str(uuid4()), "--email", "foo@bar.com", "--password", "123"],
    )
    assert res.exit_code == 1
    mocked_login.assert_called_once()
    assert mocked_get_project_batch_types.call_count == 2


def test_list_project_batch_types__not_empty(mocker):
    """Test project batch types being outputed to the shell."""
    runner = CliRunner()
    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_get_project_batch_types = mocker.patch.object(
        APIClient, "get_project_batch_types", return_value=MOCKED_BATCH_TYPES
    )

    res = runner.invoke(
        list_project_batch_types,
        [str(uuid4()), "--email", "foo@bar.com", "--password", "123"],
    )
    assert res.exit_code == 0
    mocked_login.assert_called_once()
    mocked_get_project_batch_types.assert_called_once()

    output_line = io.BytesIO()
    sys.stdout = output_line
    line_one = "\t".join(
        [
            MOCKED_BATCH_TYPES["results"][0]["key"],
            MOCKED_BATCH_TYPES["results"][0]["description"],
        ]
    )
    line_two = "\t".join(
        [
            MOCKED_BATCH_TYPES["results"][1]["key"],
            MOCKED_BATCH_TYPES["results"][1]["description"],
        ]
    )
    echo("\n".join([line_one, line_two]))
    assert output_line.getvalue() == res.output.encode()
