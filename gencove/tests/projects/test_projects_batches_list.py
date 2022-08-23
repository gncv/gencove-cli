"""Test project's batches list command."""
# pylint: disable=wrong-import-order, import-error
import io
import operator
import sys
from uuid import uuid4

from click import echo
from click.testing import CliRunner

from gencove.client import APIClient, APIClientTimeout  # noqa: I100
from gencove.command.projects.cli import list_project_batches
from gencove.models import ProjectBatches
from gencove.tests.decorators import assert_authorization
from gencove.tests.filters import filter_jwt, replace_gencove_url_vcr
from gencove.tests.projects.vcr.filters import (
    filter_project_batches_request,
    filter_project_batches_response,
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
            filter_project_batches_request,
        ],
        "before_record_response": [
            filter_jwt,
            filter_volatile_dates,
            filter_project_batches_response,
        ],
    }


@pytest.mark.vcr
@assert_authorization
def test_list_project_batches__empty(credentials, mocker, project_id, recording, vcr):
    """Test project has not batches."""
    runner = CliRunner()
    if not recording:
        # Mock create_project_batch only if using the cassettes, since we
        # mock the return value.
        get_project_batches_response = get_vcr_response(
            "/api/v2/project-batches/", vcr, operator.contains
        )
        mocked_get_project_batches = mocker.patch.object(
            APIClient,
            "get_project_batches",
            return_value=ProjectBatches(**get_project_batches_response),
        )
    res = runner.invoke(
        list_project_batches,
        [project_id, *credentials],
    )
    assert res.exit_code == 0
    if not recording:
        mocked_get_project_batches.assert_called_once()
    assert res.output == ""


@pytest.mark.vcr
@assert_authorization
def test_list_project_batches__not_empty(
    credentials, mocker, project_id_batches, recording, vcr
):
    """Test project batches being outputed to the shell."""
    runner = CliRunner()
    if not recording:
        # Mock create_project_batch only if using the cassettes, since we
        # mock the return value.
        get_project_batches_response = get_vcr_response(
            "/api/v2/project-batches/", vcr, operator.contains
        )
        mocked_get_project_batches = mocker.patch.object(
            APIClient,
            "get_project_batches",
            return_value=ProjectBatches(**get_project_batches_response),
        )
    res = runner.invoke(
        list_project_batches,
        [project_id_batches, *credentials],
    )
    assert res.exit_code == 0
    if not recording:
        mocked_get_project_batches.assert_called_once()

        output_line = io.BytesIO()
        sys.stdout = output_line
        for response in ProjectBatches(**get_project_batches_response).results:
            echo(
                "\t".join(
                    [
                        str(response.id),
                        response.last_status.created.isoformat(),
                        response.last_status.status,
                        response.batch_type,
                        response.name,
                    ]
                )
            )
        assert output_line.getvalue() == res.output.encode()


@pytest.mark.default_cassette("jwt-create.yaml")
@pytest.mark.vcr
@assert_authorization
def test_list_project_batches__not_empty_slow_response_retry(credentials, mocker):
    """Test project batches slow response retry."""
    runner = CliRunner()
    mocked_get_project_batches = mocker.patch.object(
        APIClient,
        "get_project_batches",
        side_effect=APIClientTimeout("Could not connect to the api server"),
    )

    res = runner.invoke(
        list_project_batches,
        [str(uuid4()), *credentials],
    )
    assert res.exit_code == 1
    assert mocked_get_project_batches.call_count == 2
