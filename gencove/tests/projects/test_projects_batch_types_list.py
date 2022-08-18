"""Test project's batch types list command."""
# pylint: disable=wrong-import-order, import-error
import io
import operator
import sys
from uuid import uuid4

from click import echo
from click.testing import CliRunner

from gencove.client import APIClient, APIClientTimeout  # noqa: I100
from gencove.command.projects.cli import list_project_batch_types
from gencove.models import ProjectBatchTypes
from gencove.tests.decorators import assert_authorization
from gencove.tests.filters import filter_jwt, replace_gencove_url_vcr
from gencove.tests.projects.vcr.filters import (
    filter_get_project_batch_types_request,
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
            filter_get_project_batch_types_request,
        ],
        "before_record_response": [
            filter_jwt,
            filter_volatile_dates,
        ],
    }


@pytest.mark.vcr
@assert_authorization
def test_list_project_batch_types__empty(
    credentials, mocker, project_id, recording, vcr
):  # pylint: disable=unused-argument
    """Test project has not batch types."""
    runner = CliRunner()
    if not recording:
        # Mock get_project_batch_types only if using the cassettes, since we
        # mock the return value.
        get_project_batch_types_response = get_vcr_response(
            "/api/v2/project-batch-types/", vcr, operator.contains
        )
        mocked_get_project_batch_types = mocker.patch.object(
            APIClient,
            "get_project_batch_types",
            return_value=ProjectBatchTypes(**get_project_batch_types_response),
        )

    res = runner.invoke(
        list_project_batch_types,
        [project_id, *credentials],
    )
    assert res.exit_code == 0
    if not recording:
        mocked_get_project_batch_types.assert_called_once()
    assert res.output == ""


@pytest.mark.default_cassette("jwt-create.yaml")
@pytest.mark.vcr
@assert_authorization
def test_list_project_batch_types__not_empty_slow_response_retry(mocker, credentials):
    """Test project batch types being outputed to the shell."""
    runner = CliRunner()
    mocked_get_project_batch_types = mocker.patch.object(
        APIClient,
        "get_project_batch_types",
        side_effect=APIClientTimeout("Could not connect to the api server"),
    )

    res = runner.invoke(
        list_project_batch_types,
        [str(uuid4()), *credentials],
    )
    assert res.exit_code == 1
    assert mocked_get_project_batch_types.call_count == 2


@pytest.mark.vcr
@assert_authorization
def test_list_project_batch_types__not_empty(
    mocker, credentials, project_id_batches, recording, vcr
):
    """Test project batch types being outputed to the shell."""
    runner = CliRunner()
    if not recording:
        # Mock get_project_batch_types only if using the cassettes, since we
        # mock the return value.
        get_project_batch_types_response = get_vcr_response(
            "/api/v2/project-batch-types/", vcr, operator.contains
        )
        mocked_get_project_batch_types = mocker.patch.object(
            APIClient,
            "get_project_batch_types",
            return_value=ProjectBatchTypes(**get_project_batch_types_response),
        )

    res = runner.invoke(
        list_project_batch_types,
        [project_id_batches, *credentials],
    )
    assert res.exit_code == 0
    assert res.output != ""
    if not recording:
        mocked_get_project_batch_types.assert_called_once()

        output_line = io.BytesIO()
        sys.stdout = output_line
        batches_output = [
            f"{batch_type['key']}\t{batch_type['description']}"
            for batch_type in get_project_batch_types_response["results"]
        ]
        echo("\n".join(batches_output))
        assert output_line.getvalue() == res.output.encode()
