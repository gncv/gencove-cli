"""Test samples set metadata command."""

import json
from uuid import uuid4

from click.testing import CliRunner

from gencove.client import APIClient, APIClientError
from gencove.command.samples.cli import set_metadata


def test_set_metadata__bad_sample_id(mocker):
    """Test set metadata failure when non-uuid string is used as
    sample id.
    """
    runner = CliRunner()

    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_set_metadata = mocker.patch.object(
        APIClient,
        "set_metadata",
    )

    res = runner.invoke(
        set_metadata,
        [
            "1111111",
            "--email",
            "foo@bar.com",
            "--password",
            "123",
            "--json",
            '{"somekey":"somevalue"}',
        ],
    )

    assert res.exit_code == 1
    mocked_login.assert_called_once()
    mocked_set_metadata.assert_not_called()
    assert "Sample ID is not valid" in res.output


def test_set_metadata__not_owned_sample(mocker):
    """Test set metadata failure when sample is not owned."""
    mocked_response = {"detail": "Not found."}

    runner = CliRunner()

    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_set_metadata = mocker.patch.object(
        APIClient,
        "set_metadata",
        return_value=mocked_response,
        side_effect=APIClientError(message="", status_code=404),
    )

    res = runner.invoke(
        set_metadata,
        [
            str(uuid4()),
            "--email",
            "foo@bar.com",
            "--password",
            "123",
            "--json",
            '{"somekey":"somevalue"}',
        ],
    )
    assert res.exit_code == 1
    mocked_login.assert_called_once()
    mocked_set_metadata.assert_called_once()
    assert "you do not have permission required" in res.output


def test_set_metadata__bad_json(mocker):
    """Test sample set metadata bad json failure."""
    sample_id = str(uuid4())

    runner = CliRunner()

    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_set_metadata = mocker.patch.object(
        APIClient,
        "set_metadata",
    )

    res = runner.invoke(
        set_metadata,
        [
            sample_id,
            "--email",
            "foo@bar.com",
            "--password",
            "123",
            "--json",
            '{"somekey": "somevalue"',
        ],
    )
    assert res.exit_code == 1
    mocked_login.assert_called_once()
    mocked_set_metadata.assert_not_called()
    assert "Metadata JSON is not valid" in res.output


def test_set_metadata__success(mocker):
    """Test sample set metadata success."""
    sample_id = str(uuid4())

    runner = CliRunner()

    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_set_metadata = mocker.patch.object(
        APIClient,
        "set_metadata",
    )
    payload = '{"somekey": "somevalue"}'
    res = runner.invoke(
        set_metadata,
        [
            sample_id,
            "--email",
            "foo@bar.com",
            "--password",
            "123",
            "--json",
            payload,
        ],
    )
    assert res.exit_code == 0
    mocked_login.assert_called_once()
    mocked_set_metadata.assert_called_once_with(
        sample_id, json.loads(payload)
    )
    assert "Assigned metadata to a sample {}".format(sample_id) in res.output
