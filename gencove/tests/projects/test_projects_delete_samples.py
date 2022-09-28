"""Test project's delete samples command."""
# pylint: disable=wrong-import-order, import-error
import operator
from uuid import uuid4

from click.testing import CliRunner

from gencove.client import (
    APIClient,
    APIClientError,
)  # noqa: I100
from gencove.command.projects.cli import delete_project_samples
from gencove.exceptions import MaintenanceError
from gencove.tests.decorators import assert_authorization, assert_no_requests
from gencove.tests.filters import filter_jwt, replace_gencove_url_vcr
from gencove.tests.projects.vcr.filters import (
    filter_project_delete_samples,
)
from gencove.tests.upload.vcr.filters import filter_volatile_dates
from gencove.tests.utils import get_vcr_response

import pytest

from vcr import VCR


@pytest.fixture(scope="module")
def vcr_config():
    """VCR configuration."""
    return {
        "cassette_library_dir": "gencove/tests/projects/vcr",
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
            filter_project_delete_samples,
        ],
        "before_record_response": [
            filter_jwt,
            filter_volatile_dates,
        ],
    }


@assert_no_requests
def test_delete_project_samples__bad_project_id(
    mocker, credentials
):  # pylint: disable=unused-argument
    """Test delete project samples when non-uuid string is used as project
    id."""
    runner = CliRunner()

    res = runner.invoke(
        delete_project_samples,
        [
            "22222222",
            *credentials,
            "--sample-ids",
            "11111111-1111-1111-1111-111111111111,"
            "22222222-2222-2222-2222-222222222222",
        ],
    )
    assert res.exit_code == 1
    assert "Project ID is not valid" in res.output


@pytest.mark.default_cassette("jwt-create.yaml")
@pytest.mark.vcr
@assert_authorization
def test_delete_project_samples__not_owned_project(credentials, mocker):
    """Test delete project samples failure when project is not owned."""
    runner = CliRunner()
    mocked_delete_project_samples = mocker.patch.object(
        APIClient,
        "delete_project_samples",
        side_effect=APIClientError(message="", status_code=403),
    )

    res = runner.invoke(
        delete_project_samples,
        [
            str(uuid4()),
            *credentials,
            "--sample-ids",
            "11111111-1111-1111-1111-111111111111,"
            "22222222-2222-2222-2222-222222222222",
        ],
    )
    assert res.exit_code == 1
    mocked_delete_project_samples.assert_called_once()
    assert "You do not have the sufficient permission" in res.output


@pytest.mark.vcr
@assert_authorization
def test_delete_project_samples__success__empty_sample_ids(
    credentials, mocker, project_id, recording, vcr
):
    """Test delete project samples success when an empty list of sample ids
    is sent."""

    runner = CliRunner()
    if not recording:
        # Mock delete_project_samples only if using the cassettes, since we
        # mock the return value.
        delete_project_samples_response = get_vcr_response(
            "/api/v2/project-delete-samples/", vcr, operator.contains
        )
        mocked_delete_project_samples = mocker.patch.object(
            APIClient,
            "delete_project_samples",
            return_value=delete_project_samples_response,
        )

    res = runner.invoke(
        delete_project_samples,
        [
            project_id,
            *credentials,
            "--sample-ids",
            "",
        ],
    )
    assert res.exit_code == 0
    if not recording:
        mocked_delete_project_samples.assert_called_once()
    assert "The following samples have been deleted successfully" in res.output


@assert_no_requests
def test_delete_project_samples__invalid_sample_ids(
    credentials, mocker
):  # pylint: disable=unused-argument
    """Test delete project samples failure when an invalid list of sample ids
    is sent."""

    runner = CliRunner()

    res = runner.invoke(
        delete_project_samples,
        [
            str(uuid4()),
            *credentials,
            "--sample-ids",
            "1111,222",
        ],
    )
    assert res.exit_code == 1
    assert "Not all sample IDs are valid" in res.output


@pytest.mark.vcr
@assert_authorization
def test_delete_project_samples__sample_not_in_project(
    credentials, mocker, project_id, recording, vcr
):
    """Test delete project samples with sample not in project."""

    runner = CliRunner()
    if not recording:
        # Mock delete_project_samples only if using the cassettes, since we
        # mock the return value.
        delete_project_samples_response = get_vcr_response(
            "/api/v2/project-delete-samples/",
            vcr,
            operator.contains,
            just_body=False,
        )
        mocked_delete_project_samples = mocker.patch.object(
            APIClient,
            "delete_project_samples",
            side_effect=APIClientError(
                message=delete_project_samples_response["body"]["string"],
                status_code=delete_project_samples_response["status"]["code"],
            ),
        )
    res = runner.invoke(
        delete_project_samples,
        [
            project_id,
            *credentials,
            "--sample-ids",
            "11111111-1111-1111-1111-111111111111",
        ],
    )
    assert res.exit_code == 0
    if not recording:
        mocked_delete_project_samples.assert_called_once()
    assert "All sample ids must be part of the current project." in res.output


@pytest.mark.vcr
@assert_authorization
@pytest.mark.default_cassette("test_delete_project_samples__success.yaml")
@pytest.mark.parametrize("remove_hyphens", [True, False])
def test_delete_project_samples__success(  # pylint: disable=too-many-arguments
    deleted_sample, credentials, mocker, project_id, recording, vcr, remove_hyphens
):
    """Test delete project samples success."""
    runner = CliRunner()
    if not recording:
        # Mock delete_project_samples only if using the cassettes, since we
        # mock the return value.
        delete_project_samples_response = get_vcr_response(
            "/api/v2/project-delete-samples/", vcr, operator.contains
        )
        mocked_delete_project_samples = mocker.patch.object(
            APIClient,
            "delete_project_samples",
            return_value=delete_project_samples_response,
        )

    if remove_hyphens:
        project_id = project_id.replace("-", "")

    res = runner.invoke(
        delete_project_samples,
        [
            project_id,
            *credentials,
            "--sample-ids",
            deleted_sample,
        ],
    )
    assert res.exit_code == 0
    if not recording:
        mocked_delete_project_samples.assert_called_once()
    assert "The following samples have been deleted successfully" in res.output


@pytest.mark.vcr
@assert_authorization
@pytest.mark.default_cassette(
    "test_delete_project_samples__returns_maintenance_error_503.yaml"
)
def test_delete_project_samples__returns_maintenance_error_503(
    # pylint: disable=too-many-arguments
    deleted_sample,
    credentials,
    mocker,
    project_id,
    recording,
    using_api_key,
    vcr,
):
    """Test delete project samples success."""
    runner = CliRunner()
    if not recording:
        # Mock delete_project_samples only if using the cassettes, since we
        # mock the return value.

        delete_project_samples_response = get_vcr_response(
            "/api/v2/project-delete-samples/", vcr, operator.contains
        )
        mocked_delete_project_samples = mocker.patch.object(
            APIClient,
            "delete_project_samples",
            side_effect=MaintenanceError(
                message=delete_project_samples_response["maintenance_message"],
                eta=delete_project_samples_response["maintenance_eta"],
            ),
        )

    res = runner.invoke(
        delete_project_samples,
        [
            project_id,
            *credentials,
            "--sample-ids",
            deleted_sample,
        ],
    )
    assert res.exit_code == 1
    if not recording:
        if using_api_key:
            mocked_delete_project_samples.assert_called_once()
        else:
            mocked_delete_project_samples.assert_not_called()

    assert (
        "ERROR: Gencove is currently undergoing maintenance and "
        "will return at the given ETA. "
        "Thank you for your patience."
    ) in res.output
