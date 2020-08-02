"""Test project's batches create command."""

import io
import sys
from uuid import uuid4

from click import echo
from click.testing import CliRunner

from gencove.client import APIClient, APIClientError  # noqa: I100
from gencove.command.projects.cli import create_project_batch


def test_create_project_batches__missing_batch_type(mocker):
    runner = CliRunner()
    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_create_project_batch = mocker.patch.object(
        APIClient, "create_project_batch",
    )
    res = runner.invoke(
        create_project_batch,
        [
            str(uuid4()),
            "--email",
            "foo@bar.com",
            "--password",
            "123",
            "--batch-name",
            "foo bar",
        ],
    )
    assert res.exit_code == 0
    mocked_login.assert_called_once()
    mocked_create_project_batch.assert_not_called()
    assert "You must provide value for --batch-type" in res.output


def test_create_project_batches__missing_batch_name(mocker):
    runner = CliRunner()
    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_create_project_batch = mocker.patch.object(
        APIClient, "create_project_batch",
    )
    res = runner.invoke(
        create_project_batch,
        [
            str(uuid4()),
            "--email",
            "foo@bar.com",
            "--password",
            "123",
            "--batch-type",
            "hd777k",
        ],
    )
    assert res.exit_code == 0
    mocked_login.assert_called_once()
    mocked_create_project_batch.assert_not_called()
    assert "You must provide value for --batch-name" in res.output


def test_create_project_batches__bad_project_id(mocker):
    runner = CliRunner()
    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_create_project_batch = mocker.patch.object(
        APIClient, "create_project_batch",
    )
    res = runner.invoke(
        create_project_batch,
        [
            "1111111",
            "--email",
            "foo@bar.com",
            "--password",
            "123",
            "--batch-type",
            "hd777k",
            "--batch-name",
            "foo bar",
        ],
    )
    assert res.exit_code == 0
    mocked_login.assert_called_once()
    mocked_create_project_batch.assert_not_called()
    assert "Project ID is not valid" in res.output


def test_create_project_batches__not_owned_project(mocker):
    """Test project batch types being outputed to the shell."""
    MOCKED_RESPONSE = {"detail": "Not found."}

    runner = CliRunner()
    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_create_project_batch = mocker.patch.object(
        APIClient, "create_project_batch", return_value=MOCKED_RESPONSE
    )

    mocked_create_project_batch = mocker.patch.object(
        APIClient,
        "create_project_batch",
        side_effect=APIClientError(message="", status_code=404),
    )

    res = runner.invoke(
        create_project_batch,
        [
            str(uuid4()),
            "--email",
            "foo@bar.com",
            "--password",
            "123",
            "--batch-type",
            "hd777k",
            "--batch-name",
            "foo bar",
        ],
    )
    assert res.exit_code == 0
    mocked_login.assert_called_once()
    mocked_create_project_batch.assert_called_once()
    assert "you do not have permission required" in res.output


def test_create_project_batches__duplicate_client_ids(mocker):
    """Test project batch types being outputed to the shell."""
    MOCKED_RESPONSE = {
        "sample_ids": ["All samples must have unique client_id attribute."],
        "duplicate_client_ids": {
            "cow1": [
                "85b3d2c4-7215-4fb0-9cc6-5731bae71ea2",
                "01dc9ad3-f05d-40bb-967f-715e03cb2108",
            ]
        },
    }

    runner = CliRunner()
    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_create_project_batch = mocker.patch.object(
        APIClient, "create_project_batch", return_value=MOCKED_RESPONSE
    )

    mocked_create_project_batch = mocker.patch.object(
        APIClient,
        "create_project_batch",
        side_effect=APIClientError(message="", status_code=400),
    )

    res = runner.invoke(
        create_project_batch,
        [
            str(uuid4()),
            "--email",
            "foo@bar.com",
            "--password",
            "123",
            "--batch-type",
            "hd777k",
            "--batch-name",
            "foo bar",
        ],
    )
    assert res.exit_code == 0
    mocked_login.assert_called_once()
    mocked_create_project_batch.assert_called_once()
    assert "There was an error creating project batches" in res.output


def test_create_project_batches__success__with_sample_ids(mocker):
    MOCKED_RESPONSE = {
        "meta": {"count": 1},
        "results": [
            {"id": str(uuid4()), "name": "foo bar", "batch_type": "hd777k"}
        ],
    }

    runner = CliRunner()
    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_create_project_batch = mocker.patch.object(
        APIClient, "create_project_batch", return_value=MOCKED_RESPONSE
    )

    res = runner.invoke(
        create_project_batch,
        [
            str(uuid4()),
            "--email",
            "foo@bar.com",
            "--password",
            "123",
            "--batch-type",
            "hd777k",
            "--batch-name",
            "foo bar",
            "--sample-ids",
            "11111111-1111-1111-1111-111111111111,22222222-2222-2222-2222-222222222222",  # noqa
        ],
    )
    assert res.exit_code == 0
    mocked_login.assert_called_once()
    mocked_create_project_batch.assert_called_once()

    output_line = io.BytesIO()
    sys.stdout = output_line
    echo(
        "\t".join(
            [
                MOCKED_RESPONSE["results"][0]["id"],
                MOCKED_RESPONSE["results"][0]["batch_type"],
                MOCKED_RESPONSE["results"][0]["name"],
            ]
        )
    )
    assert output_line.getvalue() == res.output.encode()


def test_create_project_batches__success__without_sample_ids(mocker):
    MOCKED_RESPONSE = {
        "meta": {"count": 1},
        "results": [
            {"id": str(uuid4()), "name": "foo bar", "batch_type": "hd777k"}
        ],
    }

    runner = CliRunner()
    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_create_project_batch = mocker.patch.object(
        APIClient, "create_project_batch", return_value=MOCKED_RESPONSE
    )

    res = runner.invoke(
        create_project_batch,
        [
            str(uuid4()),
            "--email",
            "foo@bar.com",
            "--password",
            "123",
            "--batch-type",
            "hd777k",
            "--batch-name",
            "foo bar",
        ],
    )
    assert res.exit_code == 0
    mocked_login.assert_called_once()
    mocked_create_project_batch.assert_called_once()

    output_line = io.BytesIO()
    sys.stdout = output_line
    echo(
        "\t".join(
            [
                MOCKED_RESPONSE["results"][0]["id"],
                MOCKED_RESPONSE["results"][0]["batch_type"],
                MOCKED_RESPONSE["results"][0]["name"],
            ]
        )
    )
    assert output_line.getvalue() == res.output.encode()
