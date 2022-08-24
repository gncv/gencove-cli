"""Test project list command."""
# pylint: disable=wrong-import-order, import-error
import io
import operator
import os
import sys
from datetime import datetime, timedelta
from platform import platform
from uuid import uuid4

import boto3

from click import echo
from click.testing import CliRunner

from gencove.client import (
    APIClient,
    APIClientError,
    APIClientTimeout,
)  # noqa: I100
from gencove.command.projects.cli import list_projects
from gencove.models import (
    PipelineCapabilities,
    Project,
    Projects,
)
from gencove.tests.decorators import assert_authorization
from gencove.tests.filters import filter_jwt, replace_gencove_url_vcr
from gencove.tests.projects.vcr.filters import (
    filter_list_projects_response,
    filter_pipeline_capabilities_request,
    filter_pipeline_capabilities_response,
)
from gencove.tests.upload.vcr.filters import filter_volatile_dates
from gencove.tests.utils import get_vcr_response
from gencove.version import version

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
            filter_pipeline_capabilities_request,
        ],
        "before_record_response": [
            filter_jwt,
            filter_volatile_dates,
            filter_list_projects_response,
            filter_pipeline_capabilities_response,
        ],
    }


@pytest.mark.default_cassette("jwt-create.yaml")
@pytest.mark.vcr
@assert_authorization
def test_list_empty(mocker, credentials):
    """Test user organization has no projects."""
    runner = CliRunner()
    mocked_get_projects = mocker.patch.object(
        APIClient,
        "list_projects",
        return_value=Projects(results=[], meta=dict(next=None)),
    )
    res = runner.invoke(list_projects, credentials)
    assert res.exit_code == 0
    mocked_get_projects.assert_called_once()
    assert "" in res.output


MOCKED_PIPELINE_CAPABILITY = {
    "id": str(uuid4()),
    "name": "test capability",
    "private": False,
    "merge_vcfs_enabled": False,
}


@pytest.mark.default_cassette("jwt-create.yaml")
@pytest.mark.vcr
@assert_authorization
def test_list_projects_no_permission(mocker, credentials):
    """Test projects no permission available to show them."""
    runner = CliRunner()
    mocked_get_projects = mocker.patch.object(
        APIClient,
        "list_projects",
        side_effect=APIClientError(
            message="API Client Error: Not Found: Not found.", status_code=403
        ),
        return_value={"detail": "Not found"},
    )
    mocked_get_pipeline_capabilities = mocker.patch.object(
        APIClient, "get_pipeline_capabilities"
    )
    res = runner.invoke(list_projects, credentials)
    assert res.exit_code == 1
    mocked_get_projects.assert_called_once()
    mocked_get_pipeline_capabilities.assert_not_called()

    output_line = io.BytesIO()
    sys.stdout = output_line
    echo(
        "\n".join(
            [
                "ERROR: You do not have the sufficient permission "
                "level required to perform this operation.",
                "ERROR: API Client Error: Not Found: Not found.",
                "Aborted!",
            ]
        )
    )
    assert output_line.getvalue() == res.output.encode()


@pytest.mark.default_cassette("jwt-create.yaml")
@pytest.mark.vcr
@assert_authorization
def test_list_projects_slow_response_retry_list(mocker, credentials):
    """Test projects slow response retry on the list."""
    runner = CliRunner()
    mocked_get_projects = mocker.patch.object(
        APIClient,
        "list_projects",
        side_effect=APIClientTimeout("Could not connect to the api server"),
    )
    mocked_get_pipeline_capabilities = mocker.patch.object(
        APIClient, "get_pipeline_capabilities"
    )
    res = runner.invoke(list_projects, credentials)
    assert res.exit_code == 1
    assert mocked_get_projects.call_count == 2
    mocked_get_pipeline_capabilities.assert_not_called()


@pytest.mark.default_cassette("jwt-create.yaml")
@pytest.mark.vcr
@assert_authorization
def test_list_projects_slow_response_dump_log(mocker, credentials, dump_filename):
    """Test projects slow response dumps a log filet."""
    del os.environ["GENCOVE_SAVE_DUMP_LOG"]
    runner = CliRunner()
    mocker.patch.object(
        APIClient,
        "list_projects",
        side_effect=APIClientTimeout("Could not connect to the api server"),
    )
    python_version = sys.version_info
    logs = [
        f"Python version: {python_version.major}.{python_version.minor}.{python_version.micro}",  # noqa: E501  # pylint: disable=line-too-long
        f"CLI version: {version()}",
        f"OS details: {platform()}",
        f"boto3 version: {boto3.__version__}",
        "Retrieving projects",
        "Get projects page",
        "Could not connect to the api server",
    ]
    with runner.isolated_filesystem():
        res = runner.invoke(list_projects, credentials)
        assert res.exit_code == 1
        assert (
            f"Please attach the debug log file located in {dump_filename} to a bug report."  # noqa: E501  # pylint: disable=line-too-long
            in res.output
        )
        with open(dump_filename, encoding="utf8") as log_file:
            log_content = log_file.read()
            for log in logs:
                assert log in log_content


@pytest.mark.vcr
@assert_authorization
def test_list_projects_slow_response_retry_pipeline(
    mocker, credentials, recording, vcr
):
    """Test projects slow repsonse retry on the pipeline capabilities."""
    runner = CliRunner()
    if not recording:
        # Mock list_projects only if using the cassettes, since we mock the
        # return value.
        list_projects_response = get_vcr_response("/api/v2/projects/", vcr)
        mocked_get_projects = mocker.patch.object(
            APIClient,
            "list_projects",
            return_value=Projects(**list_projects_response),
        )
    mocked_get_pipeline_capabilities = mocker.patch.object(
        APIClient,
        "get_pipeline_capabilities",
        side_effect=APIClientTimeout("Could not connect to the api server"),
    )
    res = runner.invoke(list_projects, credentials)
    assert res.exit_code == 1
    if not recording:
        mocked_get_projects.assert_called_once()
    assert mocked_get_pipeline_capabilities.call_count == 3


@pytest.mark.vcr
@assert_authorization
def test_list_projects(mocker, credentials, recording, vcr):
    """Test projects being outputed to the shell."""
    runner = CliRunner()
    if not recording:
        # Mock list_projects only if using the cassettes, since we mock the
        # return value.
        list_projects_response = get_vcr_response("/api/v2/projects/", vcr)
        mocked_get_projects = mocker.patch.object(
            APIClient,
            "list_projects",
            return_value=Projects(**list_projects_response),
        )
        get_pipeline_capabilities_response = get_vcr_response(
            "/api/v2/pipeline-capabilities/", vcr, operator.contains
        )
        mocked_get_pipeline_capabilities = mocker.patch.object(
            APIClient,
            "get_pipeline_capabilities",
            return_value=PipelineCapabilities(**get_pipeline_capabilities_response),
        )
    res = runner.invoke(list_projects, credentials)
    assert res.exit_code == 0
    if not recording:
        mocked_get_projects.assert_called_once()
        projects = list_projects_response["results"]
        assert mocked_get_pipeline_capabilities.call_count == len(projects)
        output_line = io.BytesIO()
        sys.stdout = output_line
        for project in projects:
            project = Project(**project)
            echo(
                "\t".join(
                    [
                        str(project.created),
                        str(project.id),
                        project.name.replace("\t", " "),
                        get_pipeline_capabilities_response["name"],
                    ]
                )
            )
        assert output_line.getvalue() == res.output.encode()


# API responses may return new keys and values eventually
MOCKED_PROJECTS_WITH_UNEXPECTED_KEYS = dict(
    meta=dict(next=None),
    results=[
        {
            "id": str(uuid4()),
            "name": "test\tproject",
            "description": "",
            "created": (datetime.utcnow() - timedelta(days=7)).isoformat(),
            "organization": str(uuid4()),
            "webhook_url": "",
            "sample_count": 1,
            "pipeline_capabilities": str(uuid4()),
            "roles": [],
            **{"unexpected_key" + str(uuid4()): i for i in range(10)},
        }
    ],
)


@pytest.mark.default_cassette("jwt-create.yaml")
@pytest.mark.vcr
@assert_authorization
def test_list_projects__with_unexpected_keys(mocker, credentials):
    """Test projects being outputed to the shell where webhook_url, roles and
    some randomly generated values are part of the response.
    """

    runner = CliRunner()
    mocked_get_projects = mocker.patch.object(
        APIClient,
        "list_projects",
        return_value=Projects(**MOCKED_PROJECTS_WITH_UNEXPECTED_KEYS),
    )
    mocked_get_pipeline_capabilities = mocker.patch.object(
        APIClient,
        "get_pipeline_capabilities",
        return_value=PipelineCapabilities(**MOCKED_PIPELINE_CAPABILITY),
    )
    res = runner.invoke(list_projects, credentials)
    assert res.exit_code == 0
    mocked_get_projects.assert_called_once()
    mocked_get_pipeline_capabilities.assert_called_once()

    project = Project(**MOCKED_PROJECTS_WITH_UNEXPECTED_KEYS["results"][0])
    pipeline = PipelineCapabilities(**MOCKED_PIPELINE_CAPABILITY)

    output_line = io.BytesIO()
    sys.stdout = output_line
    echo(
        "\t".join(
            [
                str(project.created),
                str(project.id),
                project.name.replace("\t", " "),
                pipeline.name,
            ]
        )
    )
    assert output_line.getvalue() == res.output.encode()
