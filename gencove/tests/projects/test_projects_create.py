"""Test project's batches create command."""
# pylint: disable=wrong-import-order, import-error
import io
import operator
import sys
import uuid

from click import echo
from click.testing import CliRunner

from gencove.client import APIClient, APIClientError  # noqa: I100
from gencove.command.projects.cli import create_project
from gencove.command.utils import sanitize_string
from gencove.models import Project
from gencove.tests.decorators import assert_authorization
from gencove.tests.filters import filter_jwt, replace_gencove_url_vcr
from gencove.tests.projects.vcr.filters import (
    filter_create_project_request,
    filter_create_project_response,
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
            filter_create_project_request,
        ],
        "before_record_response": [
            filter_jwt,
            filter_volatile_dates,
            filter_create_project_response,
        ],
    }


def test_create_project__bad_pipeline_capability_id(credentials, mocker):
    """Test project creation failure when non-uuid string is used as
    pipeline capability id.
    """
    runner = CliRunner()
    mocked_create_project = mocker.patch.object(
        APIClient,
        "create_project",
    )
    res = runner.invoke(
        create_project,
        [
            "foo",
            "1111111",
            *credentials,
        ],
    )
    assert res.exit_code == 1
    mocked_create_project.assert_not_called()
    assert "Pipeline capability ID is not valid" in res.output


@pytest.mark.vcr
@assert_authorization
def test_create_project__no_pipeline_capability(credentials, mocker, recording):
    """Test project creation failure when there's no pipeline capability."""
    runner = CliRunner()
    if not recording:
        mocked_create_project = mocker.patch.object(
            APIClient,
            "create_project",
            side_effect=APIClientError(message="", status_code=400),
        )

    res = runner.invoke(
        create_project,
        [
            "foo",
            str(uuid.uuid4()),
            *credentials,
        ],
    )
    assert res.exit_code == 1
    if not recording:
        mocked_create_project.assert_called_once()
        assert "WARNING: There was an error creating a project." in res.output


@pytest.mark.vcr
@assert_authorization
def test_create_project__success(
    credentials,
    mocker,
    pipeline_capability_id,
    recording,
    vcr,
):
    """Test project creation success."""
    runner = CliRunner()
    if not recording:
        # Mock create_project only if using the cassettes, since we
        # mock the return value.
        create_project_response = get_vcr_response(
            "/api/v2/projects/", vcr, operator.contains
        )
        mocked_create_project = mocker.patch.object(
            APIClient,
            "create_project",
            return_value=Project(**create_project_response),
        )
    res = runner.invoke(
        create_project,
        [
            "Test create project",
            pipeline_capability_id,
            *credentials,
        ],
    )
    assert res.exit_code == 0
    if not recording:
        mocked_create_project.assert_called_once()

        output_line = io.BytesIO()
        sys.stdout = output_line
        project = Project(**create_project_response)
        echo(
            "\t".join(
                [
                    str(project.created),
                    str(project.id),
                    sanitize_string(project.name),
                    str(project.pipeline_capabilities),
                ]
            )
        )
        assert output_line.getvalue() == res.output.encode()
