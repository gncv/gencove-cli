"""Test project list samples command."""
# pylint: disable=wrong-import-order, import-error
import io
import operator
import sys
from uuid import uuid4

from click.testing import CliRunner

from gencove.client import APIClient, APIClientError, APIClientTimeout
from gencove.command.projects.cli import list_project_samples
from gencove.logger import echo_data
from gencove.models import ProjectSamples, SampleDetails
from gencove.tests.decorators import assert_authorization, assert_no_requests
from gencove.tests.filters import filter_jwt, replace_gencove_url_vcr
from gencove.tests.projects.vcr.filters import (
    filter_get_project_samples_request,
    filter_get_project_samples_response,
)
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
            filter_get_project_samples_request,
        ],
        "before_record_response": [
            filter_jwt,
            filter_get_project_samples_response,
        ],
    }


@pytest.mark.default_cassette("jwt-create.yaml")
@pytest.mark.vcr
@assert_authorization
def test_list_empty(mocker, credentials, project_id):
    """Test project has no samples."""
    runner = CliRunner()
    mocked_get_project_samples = mocker.patch.object(
        APIClient,
        "get_project_samples",
        return_value=ProjectSamples(results=[], meta=dict(next=None)),
    )
    res = runner.invoke(
        list_project_samples,
        [project_id, *credentials],
    )
    assert res.exit_code == 0
    mocked_get_project_samples.assert_called_once()
    assert res.output == ""


@assert_no_requests
def test_list_projects_bad_project_id(
    mocker, credentials
):  # pylint: disable=unused-argument
    """Test project samples throw an error if project id is not uuid."""
    runner = CliRunner()

    project_id = "123456"

    res = runner.invoke(
        list_project_samples,
        [project_id, *credentials],
    )
    assert res.exit_code == 1
    output_line = io.BytesIO()
    sys.stdout = output_line
    echo_data(
        "\n".join(
            [
                "ERROR: Project ID is not valid. Exiting.",
                "Aborted!",
            ]
        )
    )
    assert output_line.getvalue() == res.output.encode()


@pytest.mark.default_cassette("jwt-create.yaml")
@pytest.mark.vcr
@assert_authorization
def test_list_projects_no_project(mocker, credentials):
    """Test project samples throw an error if no project available."""
    runner = CliRunner()
    mocked_get_project_samples = mocker.patch.object(
        APIClient,
        "get_project_samples",
        side_effect=APIClientError(
            message="API Client Error: Not Found: Not found.", status_code=404
        ),
        return_value={"detail": "Not found"},
    )

    project_id = str(uuid4())

    res = runner.invoke(
        list_project_samples,
        [project_id, *credentials],
    )
    assert res.exit_code == 1
    mocked_get_project_samples.assert_called_once()

    output_line = io.BytesIO()
    sys.stdout = output_line
    echo_data(
        "\n".join(
            [
                f"ERROR: Project {project_id} does not exist.",
                "ERROR: API Client Error: Not Found: Not found.",
                "Aborted!",
            ]
        )
    )
    assert output_line.getvalue() == res.output.encode()


@pytest.mark.default_cassette("jwt-create.yaml")
@pytest.mark.vcr
@assert_authorization
def test_list_project_samples_slow_response_retry(mocker, credentials):
    """Test project samples slow response retry."""
    runner = CliRunner()
    mocked_get_project_samples = mocker.patch.object(
        APIClient,
        "get_project_samples",
        side_effect=APIClientTimeout("Could not connect to the api server"),
    )

    res = runner.invoke(
        list_project_samples,
        [str(uuid4()), *credentials],
    )
    assert res.exit_code == 1
    assert mocked_get_project_samples.call_count == 2


@pytest.mark.vcr
@assert_authorization
def test_list_project_samples(
    mocker, credentials, project_id, recording, vcr
):  # pylint: disable=unused-argument
    """Test project samples being outputed to the shell."""
    runner = CliRunner()

    if not recording:
        # Mock get_project_samples only if using the cassettes,
        # since we mock the return value.
        mocked_samples = get_vcr_response(
            "/api/v2/project-samples/", vcr, operator.contains
        )
        mocked_get_project_samples = mocker.patch.object(
            APIClient,
            "get_project_samples",
            return_value=ProjectSamples(**mocked_samples),
        )
    res = runner.invoke(
        list_project_samples,
        [project_id, *credentials],
    )
    assert res.exit_code == 0
    if not recording:
        mocked_get_project_samples.assert_called_once()
        output_line = io.BytesIO()
        sys.stdout = output_line
        for mocked_sample in mocked_samples["results"]:
            mocked_sample = SampleDetails(**mocked_sample)
            echo_data(
                "\t".join(
                    [
                        str(mocked_sample.last_status.created.isoformat()),
                        str(mocked_sample.id),
                        mocked_sample.client_id,
                        mocked_sample.last_status.status,
                        mocked_sample.archive_last_status.status,
                    ]
                )
            )
        assert output_line.getvalue() == res.output.encode()


def test_list_project_samples__archive_status_null__prints_without_fail(
    mocker, credentials, project_id, sample_archive_status_null, using_api_key
):
    """Test project samples being outputed to the shell."""
    runner = CliRunner()

    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_get_project_samples = mocker.patch.object(
        APIClient,
        "get_project_samples",
        return_value=ProjectSamples(**sample_archive_status_null),
    )
    res = runner.invoke(
        list_project_samples,
        [project_id, *credentials],
    )
    assert res.exit_code == 0

    if not using_api_key:
        mocked_login.assert_called_once()

    mocked_get_project_samples.assert_called_once()
    mocked_sample = SampleDetails(**sample_archive_status_null["results"][0])

    assert res.output.strip() == "\t".join(
        [
            str(mocked_sample.last_status.created.isoformat()),
            str(mocked_sample.id),
            mocked_sample.client_id,
            mocked_sample.last_status.status,
            "unknown",
        ]
    )
