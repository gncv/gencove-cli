"""Tests upload command of Gencove CLI."""
# pylint: disable=wrong-import-order, import-error

from click.testing import CliRunner

from gencove.client import APIClient, APIClientError
from gencove.command.basespace.autoimports.create.cli import (
    create,
)
from gencove.tests.decorators import assert_authorization
from gencove.tests.filters import filter_jwt, replace_gencove_url_vcr
from gencove.tests.utils import MOCK_UUID

import pytest

from vcr import VCR


@pytest.fixture(scope="module")
def vcr_config():
    """VCR configuration."""
    return {
        "cassette_library_dir": "gencove/tests/basespace/vcr",
        "filter_headers": [
            "Authorization",
            "Content-Length",
            "User-Agent",
        ],
        "filter_post_data_parameters": [
            ("email", "email@example.com"),
            ("password", "mock_password"),
        ],
        "match_on": ["method", "scheme", "port", "path", "query"],
        "path_transformer": VCR.ensure_suffix(".yaml"),
        "before_record_request": [
            replace_gencove_url_vcr,
        ],
        "before_record_response": [
            filter_jwt,
        ],
    }


@pytest.mark.default_cassette("jwt-create.yaml")
@pytest.mark.vcr
@assert_authorization
def test_basespace_autoimport_create_project_id_not_uuid(
    credentials,
    mocker,
):
    """Test that project id is valid UUID when creating an automated import."""
    runner = CliRunner()

    mocked_autoimport_from_basespace = mocker.patch.object(
        APIClient,
        "autoimport_from_basespace",
    )
    res = runner.invoke(
        create,
        [
            "1234",
            "identifier",
            *credentials,
        ],
    )

    assert res.exit_code == 1
    mocked_autoimport_from_basespace.assert_not_called()
    assert "ERROR: Project ID is not valid. Exiting." in res.output


@pytest.mark.default_cassette("jwt-create.yaml")
@pytest.mark.vcr
@assert_authorization
def test_basespace_autoimport_create_invalid_metadata(credentials, mocker, project_id):
    """Test that passed optional metadata is valid when creating an
    automated import.
    """
    runner = CliRunner()

    mocked_autoimport_from_basespace = mocker.patch.object(
        APIClient,
        "autoimport_from_basespace",
    )
    res = runner.invoke(
        create,
        [
            project_id,
            "identifier",
            "--metadata-json",
            "[1,2,3",
            *credentials,
        ],
    )

    assert res.exit_code == 1
    mocked_autoimport_from_basespace.assert_not_called()
    assert "ERROR: Metadata JSON is not valid. Exiting." in res.output


@pytest.mark.default_cassette("jwt-create.yaml")
@pytest.mark.vcr
@assert_authorization
def test_basespace_autoimport_create_no_permission(credentials, mocker, project_id):
    """Test that user cannot create an automated import if no permissions."""
    runner = CliRunner()

    mocked_autoimport_from_basespace = mocker.patch.object(
        APIClient,
        "autoimport_from_basespace",
        side_effect=APIClientError(message="", status_code=403),
    )
    res = runner.invoke(
        create,
        [
            project_id,
            "identifier",
            *credentials,
        ],
    )

    assert res.exit_code == 1
    mocked_autoimport_from_basespace.assert_called_once()
    assert "There was an error creating a periodic import job" in res.output


@pytest.mark.default_cassette("jwt-create.yaml")
@pytest.mark.vcr
@assert_authorization
@pytest.mark.parametrize("action", ["create", "update"])
def test_basespace_autoimport_update_with_empty_metadata(
    credentials,
    mocker,
    project_id,
    action,
):
    """Test that user can pass empty metadata when creating an
    automated import.
    """
    runner = CliRunner()

    mocked_autoimport_from_basespace = mocker.patch.object(
        APIClient,
        "autoimport_from_basespace",
        return_value={"id": MOCK_UUID, "metadata": None, "action": action},
    )
    res = runner.invoke(
        create,
        [
            project_id,
            "identifier",
            "--metadata-json",
            None,
            *credentials,
        ],
    )

    assert res.output == (
        f"Request to {action} a periodic import job of BaseSpace "
        "projects accepted.\n"
    )
    assert res.exit_code == 0
    mocked_autoimport_from_basespace.assert_called_once()


@pytest.mark.default_cassette("jwt-create.yaml")
@pytest.mark.vcr
@assert_authorization
@pytest.mark.parametrize("action", ["create", "update"])
def test_basespace_autoimport_with_metadata(credentials, mocker, project_id, action):
    """Test that user can pass optional metadata when creating an
    automated import.
    """
    runner = CliRunner()

    mocked_autoimport_from_basespace = mocker.patch.object(
        APIClient,
        "autoimport_from_basespace",
        return_value={
            "id": MOCK_UUID,
            "metadata": {"some": "metadata"},
            "action": action,
        },
    )
    res = runner.invoke(
        create,
        [
            project_id,
            "identifier",
            "--metadata-json",
            "[1,2,3]",
            *credentials,
        ],
    )

    assert res.output == (
        "Metadata will be assigned to the imported Biosamples.\n"
        f"Request to {action} a periodic import job of BaseSpace "
        "projects accepted.\n"
    )
    assert res.exit_code == 0
    mocked_autoimport_from_basespace.assert_called_once()


@pytest.mark.default_cassette("jwt-create.yaml")
@pytest.mark.vcr
@assert_authorization
@pytest.mark.parametrize("action", ["create", "update"])
def test_basespace_autoimport_update_without_metadata(
    credentials, mocker, project_id, action
):
    """Test that user can create an import job without passing metadata."""
    runner = CliRunner()

    mocked_autoimport_from_basespace = mocker.patch.object(
        APIClient,
        "autoimport_from_basespace",
        return_value={"id": MOCK_UUID, "action": action},
    )

    res = runner.invoke(
        create,
        [
            project_id,
            "identifier",
            *credentials,
        ],
    )

    assert res.output == (
        f"Request to {action} a periodic import job of BaseSpace "
        "projects accepted.\n"
    )
    assert res.exit_code == 0
    mocked_autoimport_from_basespace.assert_called_once()
