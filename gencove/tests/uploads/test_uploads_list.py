"""Test uploads list command."""
# pylint: disable=wrong-import-order, import-error

from click.testing import CliRunner

from gencove.client import APIClient, APIClientError, APIClientTimeout
from gencove.command.uploads.list.cli import list_uploads
from gencove.models import SampleSheet
from gencove.tests.decorators import assert_authorization
from gencove.tests.filters import filter_jwt, replace_gencove_url_vcr
from gencove.tests.upload.vcr.filters import (
    filter_sample_sheet_response,
    filter_volatile_dates,
)
from gencove.tests.utils import get_vcr_response

import pytest

from vcr import VCR


@pytest.fixture(scope="module")
def vcr_config():
    """VCR configuration."""
    return {
        "cassette_library_dir": "gencove/tests/uploads/vcr",
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
            filter_sample_sheet_response,
        ],
    }


@pytest.mark.vcr
@assert_authorization
def test_list_does_not_exist(mocker, credentials):
    """Test user cannot get to uploads."""
    runner = CliRunner()
    mocked_get_projects = mocker.patch.object(
        APIClient,
        "get_sample_sheet",
        side_effect=APIClientError(
            message="API Client Error: Not Found: Not found.", status_code=404
        ),
        return_value={"detail": "Not found"},
    )
    res = runner.invoke(list_uploads, credentials)
    assert isinstance(res.exception, SystemExit)
    assert res.exit_code == 1
    mocked_get_projects.assert_called_once()
    assert (
        "\n".join(
            [
                "ERROR: Uploads do not exist.",
                "ERROR: API Client Error: Not Found: Not found.",
                "Aborted!\n",
            ]
        )
        == res.output
    )


@pytest.mark.vcr
@assert_authorization
def test_list_empty(mocker, credentials):
    """Test user has no uploads."""
    runner = CliRunner()
    mocked_get_projects = mocker.patch.object(
        APIClient,
        "get_sample_sheet",
        return_value=SampleSheet(results=[], meta=dict(next=None)),
    )
    res = runner.invoke(list_uploads, credentials)
    assert res.exit_code == 0
    mocked_get_projects.assert_called_once()
    assert "" in res.output


@pytest.mark.vcr
@assert_authorization
def test_list_uploads_slow_response_retry(mocker, credentials):
    """Test list uploads slow response retry."""
    runner = CliRunner()
    mocked_get_sample_sheet = mocker.patch.object(
        APIClient,
        "get_sample_sheet",
        side_effect=APIClientTimeout("Could not connect to the api server"),
    )
    res = runner.invoke(list_uploads, credentials)
    assert res.exit_code == 1
    assert mocked_get_sample_sheet.call_count == 5
    assert res.output == "ERROR: Could not connect to the api server\nAborted!\n"


@pytest.mark.vcr
@assert_authorization
def test_list_uploads(mocker, credentials, recording, vcr):
    """Test list uploads being outputed to the shell."""
    runner = CliRunner()
    if not recording:
        sample_sheet_response = get_vcr_response("/api/v2/sample-sheet/", vcr)
        mocked_get_sample_sheet = mocker.patch.object(
            APIClient,
            "get_sample_sheet",
            return_value=SampleSheet(**sample_sheet_response),
        )
    res = runner.invoke(list_uploads, credentials)
    assert res.exit_code == 0

    if not recording:
        mocked_get_sample_sheet.assert_called()
        uploads = sample_sheet_response["results"]
        uploads = "\n".join(
            [
                "\t".join(
                    [
                        upload["client_id"],
                        upload["fastq"]["r1"]["upload"],
                        upload["fastq"]["r1"]["destination_path"],
                    ]
                )
                for upload in uploads
            ]
        )
        assert f"{uploads}\n" == res.output
