"""Test delete projects."""
# pylint: disable=wrong-import-order, import-error
import operator
from uuid import uuid4

from click.testing import CliRunner

from gencove.client import (
    APIClient,
    APIClientError,
)  # noqa: I100
from gencove.command.projects.cli import delete_projects
from gencove.exceptions import MaintenanceError
from gencove.tests.decorators import assert_authorization, assert_no_requests
from gencove.tests.filters import filter_jwt, replace_gencove_url_vcr
from gencove.tests.projects.vcr.filters import (
    filter_projects_delete,
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
            filter_projects_delete,
        ],
        "before_record_response": [
            filter_jwt,
            filter_volatile_dates,
        ],
    }


@assert_no_requests
def test_delete_projects__bad_project_id(
    mocker, credentials
):  # pylint: disable=unused-argument
    """Test delete projects when non-uuid string is used as project id."""
    runner = CliRunner()

    res = runner.invoke(
        delete_projects,
        [
            "11111111-1111-1111-1111-111111111111,22",
            *credentials,
        ],
    )
    assert res.exit_code == 1
    assert "Not all project_ids are valid." in res.output


@pytest.mark.default_cassette("jwt-create.yaml")
@pytest.mark.vcr
@assert_authorization
def test_delete_projects__not_owned_project(credentials, mocker):
    """Test delete projects failure when project is not owned."""
    runner = CliRunner()
    mocked_delete_projects = mocker.patch.object(
        APIClient,
        "delete_projects",
        side_effect=APIClientError(message="", status_code=403),
    )

    res = runner.invoke(
        delete_projects,
        [
            str(uuid4()),
            *credentials,
        ],
    )
    assert res.exit_code == 1
    mocked_delete_projects.assert_called_once()
    assert "You do not have the sufficient permission" in res.output


@assert_no_requests
def test_delete_projects__fail__empty_project_ids(
    credentials,
    mocker,  # pylint: disable=unused-argument
):
    """Test delete projects fail when an empty list of project ids is sent."""

    runner = CliRunner()

    res = runner.invoke(
        delete_projects,
        [
            "",
            *credentials,
        ],
    )
    assert res.exit_code == 1
    assert "No project ids provided" in res.output


@pytest.mark.vcr
@assert_authorization
@pytest.mark.parametrize("remove_hyphens", [True, False])
def test_delete_projects__success(  # pylint: disable=too-many-arguments
    credentials, mocker, project_id_delete, recording, vcr, remove_hyphens
):
    """Test delete projects success."""
    runner = CliRunner()
    if not recording:
        # Mock delete_projects only if using the cassettes, since we
        # mock the return value.
        delete_projects_response = get_vcr_response(
            "/api/v2/projects-delete/", vcr, operator.contains
        )
        mocked_delete_projects = mocker.patch.object(
            APIClient,
            "delete_projects",
            return_value=delete_projects_response,
        )

    if remove_hyphens:
        project_id_delete = project_id_delete.replace("-", "")

    res = runner.invoke(
        delete_projects,
        [
            project_id_delete,
            *credentials,
        ],
    )
    assert res.exit_code == 0
    if not recording:
        mocked_delete_projects.assert_called_once()
    assert "The following projects have been deleted successfully" in res.output


@pytest.mark.vcr
@assert_authorization
def test_delete_projects__returns_maintenance_error_503(
    # pylint: disable=too-many-arguments
    credentials,
    mocker,
    project_id_delete,
    recording,
    using_api_key,
    vcr,
):
    """Test delete projects maintenance error."""
    runner = CliRunner()
    if not recording:
        # Mock delete_projects only if using the cassettes, since we
        # mock the return value.

        delete_projects_resp = get_vcr_response(
            "/api/v2/projects-delete/", vcr, operator.contains
        )
        mocked_delete_projects = mocker.patch.object(
            APIClient,
            "delete_projects",
            side_effect=MaintenanceError(
                message=delete_projects_resp["maintenance_message"],
                eta=delete_projects_resp["maintenance_eta"],
            ),
        )

    res = runner.invoke(
        delete_projects,
        [
            project_id_delete,
            *credentials,
        ],
    )
    assert res.exit_code == 1
    if not recording:
        if using_api_key:
            mocked_delete_projects.assert_called_once()
        else:
            mocked_delete_projects.assert_not_called()

    assert (
        "ERROR: Gencove is currently undergoing maintenance and "
        "will return at the given ETA. "
        "Thank you for your patience."
    ) in res.output
