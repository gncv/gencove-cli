"""Test samples get metadata command."""

import io
import json
import sys
from uuid import uuid4

from click import echo
from click.testing import CliRunner

from gencove.client import APIClient, APIClientError, APIClientTimeout
from gencove.command.samples.cli import get_metadata


def test_get_metadata__bad_sample_id(mocker):
    """Test get metadata failure when non-uuid string is used as
    sample id.
    """
    runner = CliRunner()

    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_get_metadata = mocker.patch.object(
        APIClient,
        "get_metadata",
    )

    res = runner.invoke(
        get_metadata,
        [
            "1111111",
            "--email",
            "foo@bar.com",
            "--password",
            "123",
        ],
    )

    assert res.exit_code == 1
    mocked_login.assert_called_once()
    mocked_get_metadata.assert_not_called()
    assert "Sample ID is not valid" in res.output


def test_get_metadata__not_owned_sample(mocker):
    """Test get metadata failure when sample is not owned.
    This will return empty response to handle cases when using the CLI tool.
    """
    mocked_response = {"detail": "Not found."}

    runner = CliRunner()

    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_get_metadata = mocker.patch.object(
        APIClient,
        "get_metadata",
        return_value=mocked_response,
        side_effect=APIClientError(message="", status_code=404),
    )

    res = runner.invoke(
        get_metadata,
        [
            str(uuid4()),
            "--email",
            "foo@bar.com",
            "--password",
            "123",
        ],
    )
    assert res.exit_code == 1
    mocked_login.assert_called_once()
    mocked_get_metadata.assert_called_once()
    assert "you do not have permission required" in res.output


def test_get_metadata__empty(mocker):
    """Test sample doesn't have metadata."""
    sample_id = str(uuid4())

    runner = CliRunner()

    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_get_metadata = mocker.patch.object(
        APIClient,
        "get_metadata",
        return_value=dict(
            metadata=None,
        ),
    )

    res = runner.invoke(
        get_metadata,
        [
            sample_id,
            "--email",
            "foo@bar.com",
            "--password",
            "123",
        ],
    )
    assert res.exit_code == 0
    mocked_login.assert_called_once()
    mocked_get_metadata.assert_called_once()
    assert json.dumps(None, indent=4) in res.output


def test_get_metadata__success_custom_filename(mocker):
    """Test sample get metadata success to custom file."""
    sample_id = str(uuid4())

    runner = CliRunner()

    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    metadata = {"somekey": "somevalue"}
    mocked_response = {"metadata": metadata}
    mocked_get_metadata = mocker.patch.object(
        APIClient,
        "get_metadata",
        return_value=mocked_response,
    )
    custom_filename = "result.json"
    with runner.isolated_filesystem():
        res = runner.invoke(
            get_metadata,
            [
                sample_id,
                "--email",
                "foo@bar.com",
                "--password",
                "123",
                "--output-filename",
                custom_filename,
            ],
        )
        assert res.exit_code == 0
        mocked_login.assert_called_once()
        mocked_get_metadata.assert_called_once()
        with open(custom_filename, "r") as output_file:
            output_content = output_file.read()
        assert json.dumps(metadata, indent=4) == output_content


def test_get_metadata__success_nested_custom_filename(mocker):
    """Test sample get metadata success to custom file."""
    sample_id = str(uuid4())

    runner = CliRunner()

    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    metadata = {"somekey": "somevalue"}
    mocked_response = {"metadata": metadata}
    mocked_get_metadata = mocker.patch.object(
        APIClient,
        "get_metadata",
        return_value=mocked_response,
    )
    custom_filename = "somefolder/result.json"
    with runner.isolated_filesystem():
        res = runner.invoke(
            get_metadata,
            [
                sample_id,
                "--email",
                "foo@bar.com",
                "--password",
                "123",
                "--output-filename",
                custom_filename,
            ],
        )
        assert res.exit_code == 0
        mocked_login.assert_called_once()
        mocked_get_metadata.assert_called_once()
        with open(custom_filename, "r") as output_file:
            output_content = output_file.read()
        assert json.dumps(metadata, indent=4) == output_content


def test_get_metadata__success_stdout(mocker):
    """Test sample get metadata success to stdout."""
    sample_id = str(uuid4())

    runner = CliRunner()

    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    metadata = {"somekey": "somevalue"}
    mocked_response = {"metadata": metadata}
    mocked_get_metadata = mocker.patch.object(
        APIClient,
        "get_metadata",
        return_value=mocked_response,
    )

    res = runner.invoke(
        get_metadata,
        [
            sample_id,
            "--email",
            "foo@bar.com",
            "--password",
            "123",
            "--output-filename",
            "-",
        ],
    )
    assert res.exit_code == 0
    mocked_login.assert_called_once()
    mocked_get_metadata.assert_called_once()
    output_line = io.BytesIO()
    sys.stdout = output_line
    echo(json.dumps(metadata, indent=4))
    assert output_line.getvalue() in res.output.encode()


def test_get_metadata__slow_response_retry(mocker):
    """Test sample get metadata slow response retry."""
    sample_id = str(uuid4())

    runner = CliRunner()

    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    metadata = {"somekey": "somevalue"}
    mocked_get_metadata = mocker.patch.object(
        APIClient,
        "get_metadata",
        side_effect=APIClientTimeout("Could not connect to the api server"),
    )

    res = runner.invoke(
        get_metadata,
        [
            sample_id,
            "--email",
            "foo@bar.com",
            "--password",
            "123",
            "--output-filename",
            "-",
        ],
    )
    assert res.exit_code == 1
    mocked_login.assert_called_once()
    assert mocked_get_metadata.call_count == 2
    output_line = io.BytesIO()
    sys.stdout = output_line
    echo(json.dumps(metadata, indent=4))
    assert output_line.getvalue() not in res.output.encode()
