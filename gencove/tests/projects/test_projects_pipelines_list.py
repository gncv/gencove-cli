"""Test available pipelines list command."""
# pylint: disable=wrong-import-order, import-error
import operator

from click.testing import CliRunner


from gencove.client import APIClient, APIClientTimeout
from gencove.command.projects.cli import list_project_pipelines
from gencove.models import Pipelines
from gencove.tests.decorators import assert_authorization
from gencove.tests.filters import filter_jwt, replace_gencove_url_vcr
from gencove.tests.projects.vcr.filters import (
    filter_project_pipelines_response,
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
        ],
        "before_record_response": [
            filter_jwt,
            filter_volatile_dates,
            filter_project_pipelines_response,
        ],
    }


@pytest.mark.vcr
@assert_authorization
def test_list_pipelines__empty(credentials, mocker, recording, vcr):
    """Test there are no pipelines."""
    runner = CliRunner()
    if not recording:
        get_pipelines_response = get_vcr_response(
            "/api/v2/pipeline/", vcr, operator.contains
        )
        mocked_get_pipelines = mocker.patch.object(
            APIClient,
            "get_pipelines",
            return_value=Pipelines(**get_pipelines_response),
        )
    res = runner.invoke(
        list_project_pipelines,
        [*credentials],
    )
    assert res.exit_code == 0
    if not recording:
        mocked_get_pipelines.assert_called_once()
    assert res.output == ""


@pytest.mark.vcr
@assert_authorization
def test_list_pipelines__not_empty(mocker, credentials, recording, vcr):
    """Test pipelines being output to the shell."""
    runner = CliRunner()
    if not recording:
        # Mock get_pipelines only if using the cassettes, since we
        # mock the return value.
        get_pipelines_response = get_vcr_response(
            "/api/v2/pipeline/", vcr, operator.contains
        )
        get_pipelines_response["meta"]["count"] = 200
        get_pipelines_response["meta"]["next"] = None
        mocked_get_pipelines = mocker.patch.object(
            APIClient,
            "get_pipelines",
            return_value=Pipelines(**get_pipelines_response),
        )
    res = runner.invoke(
        list_project_pipelines,
        [*credentials],
    )
    assert res.exit_code == 0
    if not recording:
        mocked_get_pipelines.assert_called_once()
        pipelines = "\n".join(
            [
                f"{pipeline['id']}\t{pipeline['version']}"
                for pipeline in get_pipelines_response["results"]
            ]
        )
        assert res.output.startswith(pipelines) is True


@pytest.mark.default_cassette("jwt-create.yaml")
@pytest.mark.vcr
@assert_authorization
def test_list_pipelines__not_empty_slow_response_retry(credentials, mocker):
    """Test pipelines slow response retry."""
    runner = CliRunner()
    mocked_get_pipelines = mocker.patch.object(
        APIClient,
        "get_pipelines",
        side_effect=APIClientTimeout("Could not connect to the api server"),
    )

    res = runner.invoke(
        list_project_pipelines,
        [*credentials],
    )
    assert res.exit_code == 1
    assert mocked_get_pipelines.call_count == 2
