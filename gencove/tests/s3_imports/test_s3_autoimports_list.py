"""Test s3_imports autoimports list command."""
# pylint: disable=wrong-import-order, import-error

import pytest
from click.testing import CliRunner  # noqa: I100,I201
from gencove.client import APIClient, APIClientTimeout  # noqa: I201
from gencove.command.s3_imports.autoimports.autoimport_list.cli import (
    autoimport_list,
)
from gencove.models import S3ProjectImport
from gencove.tests.decorators import assert_authorization
from gencove.tests.filters import filter_jwt, replace_gencove_url_vcr

from vcr import VCR


@pytest.fixture(scope="module")
def vcr_config():
    """VCR configuration."""
    return {
        "cassette_library_dir": "gencove/tests/s3_imports/vcr",
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
def test_autoimport_list_empty(mocker, credentials):
    """Test user has no jobs."""
    runner = CliRunner()
    mocked_list_s3_autoimport_jobs = mocker.patch.object(
        APIClient,
        "list_s3_autoimport_jobs",
        return_value=S3ProjectImport(results=[], meta=dict(next=None)),
    )
    res = runner.invoke(autoimport_list, credentials)
    assert res.exit_code == 0
    mocked_list_s3_autoimport_jobs.assert_called_once()
    assert "" in res.output


@pytest.mark.default_cassette("jwt-create.yaml")
@pytest.mark.vcr
@assert_authorization
def test_autoimport_list_uploads_slow_response_retry(mocker, credentials):
    """Test list jobs slow response retry."""
    runner = CliRunner()
    mocked_list_s3_autoimport_jobs = mocker.patch.object(
        APIClient,
        "list_s3_autoimport_jobs",
        side_effect=APIClientTimeout("Could not connect to the api server"),
    )
    res = runner.invoke(autoimport_list, credentials)
    assert res.exit_code == 1
    assert mocked_list_s3_autoimport_jobs.call_count == 2
    assert (
        "\n".join(
            [
                "ERROR: There was an error listing S3 autoimport jobs.",
                "ERROR: Could not connect to the api server",
                "Aborted!\n",
            ]
        )
        == res.output
    )


@pytest.mark.default_cassette("jwt-create.yaml")
@pytest.mark.vcr
@assert_authorization
def test_autoimport_list(mocker, credentials):
    """Test list autoimport jobs being outputed to the shell."""
    runner = CliRunner()
    autoimport_response = {
        "meta": {"count": 2, "next": None, "previous": None},
        "results": [
            {
                "id": "41fd0397-62b0-4ef9-992f-423435b5d5ef",
                "project_id": "290e0c5a-c87e-474e-8b32-fe56fc54cc4d",
                "s3_uri": "s3://bucket/project-1/samples-1/",
                "metadata": None,
            },
            {
                "id": "0f60ab5e-a34f-4afc-a428-66f81890565f",
                "project_id": "290e0c5a-c87e-474e-8b32-fe56fc54cc4d",
                "s3_uri": "s3://bucket/project-1/samples-2/",
                "metadata": {},
            },
        ],
    }
    mocked_list_s3_autoimport_jobs = mocker.patch.object(
        APIClient,
        "list_s3_autoimport_jobs",
        return_value=S3ProjectImport(**autoimport_response),
    )
    res = runner.invoke(autoimport_list, credentials)

    assert res.exit_code == 0

    mocked_list_s3_autoimport_jobs.assert_called()
    autoimport_jobs = autoimport_response["results"]
    jobs = "\n".join(
        [
            "\t".join(
                [
                    job["id"],
                    job["project_id"],
                    job["s3_uri"],
                ]
            )
            for job in autoimport_jobs
        ]
    )
    assert f"{jobs}\n" == res.output
