"""Test available pipeline capabilities list command."""
# pylint: disable=wrong-import-order, import-error
import io
import operator
import sys
import uuid

from click.testing import CliRunner


from gencove.client import APIClient, APIClientError, APIClientTimeout
from gencove.command.projects.cli import list_project_pipeline_capabilities
from gencove.logger import echo_data
from gencove.models import PipelineDetail
from gencove.tests.decorators import assert_authorization, assert_no_requests
from gencove.tests.filters import filter_jwt, replace_gencove_url_vcr
from gencove.tests.projects.vcr.filters import (
    filter_project_pipeline_capabilities_request,
    filter_project_pipeline_capabilities_response,
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
            filter_project_pipeline_capabilities_request,
        ],
        "before_record_response": [
            filter_jwt,
            filter_volatile_dates,
            filter_project_pipeline_capabilities_response,
        ],
    }


@assert_no_requests
def test_list_pipeline_capabilities__bad_pipeline_id(
    mocker, credentials
):  # pylint: disable=unused-argument
    """Test list pipeline capabilities throw an error if pipeline id is not uuid."""
    runner = CliRunner()

    pipeline_id = "123456"

    res = runner.invoke(
        list_project_pipeline_capabilities,
        [pipeline_id, *credentials],
    )
    assert res.exit_code == 1
    output_line = io.BytesIO()
    sys.stdout = output_line
    echo_data(
        "\n".join(
            [
                "ERROR: Pipeline ID is not valid. Exiting.",
                "Aborted!",
            ]
        )
    )
    assert output_line.getvalue() == res.output.encode()


@pytest.mark.default_cassette("jwt-create.yaml")
@pytest.mark.vcr
@assert_authorization
def test_list_pipeline_capabilities__no_pipeline(mocker, credentials):
    """Test list pipeline capabilities throw an error if no pipeline available."""
    runner = CliRunner()
    mocked_get_pipeline_capabilities_for_pipeline = mocker.patch.object(
        APIClient,
        "get_pipeline_capabilities_for_pipeline",
        side_effect=APIClientError(
            message="API Client Error: Not Found: Not found.", status_code=404
        ),
        return_value={"detail": "Not found"},
    )

    pipeline_id = str(uuid.uuid4())

    res = runner.invoke(
        list_project_pipeline_capabilities,
        [pipeline_id, *credentials],
    )
    assert res.exit_code == 1
    mocked_get_pipeline_capabilities_for_pipeline.assert_called_once()

    output_line = io.BytesIO()
    sys.stdout = output_line
    echo_data(
        "\n".join(
            [
                f"ERROR: Pipeline {pipeline_id} does not exist.",
                "ERROR: API Client Error: Not Found: Not found.",
                "Aborted!",
            ]
        )
    )
    assert output_line.getvalue() == res.output.encode()


@pytest.mark.vcr
@assert_authorization
def test_list_pipeline_capabilities__empty(
    credentials, pipeline_id, mocker, recording, vcr
):
    """Test there are no pipeline capabilities."""
    # WHEN UPDATING THE CASSETTE, CHANGE THE FILE SO IT HAS AN EMPTY CAPABILITIES LIST
    runner = CliRunner()
    if not recording:
        get_pipeline_response = get_vcr_response(
            "/api/v2/pipeline/", vcr, operator.contains
        )
        mocked_get_pipeline_capabilities_for_pipeline = mocker.patch.object(
            APIClient,
            "get_pipeline_capabilities_for_pipeline",
            return_value=PipelineDetail(**get_pipeline_response),
        )
    res = runner.invoke(
        list_project_pipeline_capabilities,
        [pipeline_id, *credentials],
    )
    assert res.exit_code == 0
    if not recording:
        mocked_get_pipeline_capabilities_for_pipeline.assert_called_once()
    assert res.output == ""


@pytest.mark.vcr
@assert_authorization
def test_list_pipeline_capabilities__not_empty(
    mocker, credentials, pipeline_id, recording, vcr
):
    """Test pipeline capabilities being output to the shell."""
    runner = CliRunner()
    if not recording:
        # Mock get_pipeline_capabilities_for_pipeline only if using the cassettes,
        # since we mock the return value.
        get_pipeline_response = get_vcr_response(
            "/api/v2/pipeline/", vcr, operator.contains
        )
        mocked_get_pipeline_capabilities_for_pipeline = mocker.patch.object(
            APIClient,
            "get_pipeline_capabilities_for_pipeline",
            return_value=PipelineDetail(**get_pipeline_response),
        )
    res = runner.invoke(
        list_project_pipeline_capabilities,
        [pipeline_id, *credentials],
    )
    assert res.exit_code == 0
    if not recording:
        mocked_get_pipeline_capabilities_for_pipeline.assert_called_once()
        pipelines = "\n".join(
            [
                f"{capability['id']}\t{capability['name']}"
                for capability in get_pipeline_response["capabilities"]
            ]
        )
        assert res.output.startswith(pipelines) is True


@pytest.mark.default_cassette("jwt-create.yaml")
@pytest.mark.vcr
@assert_authorization
def test_list_pipeline_capabilities__not_empty_slow_response_retry(
    credentials, pipeline_id, mocker
):
    """Test pipeline capabilities slow response retry."""
    runner = CliRunner()
    mocked_get_pipeline_capabilities_for_pipeline = mocker.patch.object(
        APIClient,
        "get_pipeline_capabilities_for_pipeline",
        side_effect=APIClientTimeout("Could not connect to the api server"),
    )

    res = runner.invoke(
        list_project_pipeline_capabilities,
        [pipeline_id, *credentials],
    )
    assert res.exit_code == 1
    assert mocked_get_pipeline_capabilities_for_pipeline.call_count == 2
