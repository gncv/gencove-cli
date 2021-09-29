"""Test uploads list command."""
# pylint: disable=wrong-import-order, import-error
import io
import sys
from uuid import uuid4

from click import echo
from click.testing import CliRunner

from gencove.client import APIClient, APIClientError, APIClientTimeout
from gencove.command.uploads.list.cli import list_uploads
from gencove.models import SampleSheet
from gencove.tests.decorators import assert_authorization
from gencove.tests.filters import filter_jwt, replace_gencove_url_vcr
from gencove.tests.upload.vcr.filters import filter_volatile_dates

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
            # "X-Amz-Security-Token",
            # "X-Amz-Date",
        ],
        "filter_post_data_parameters": [
            ("email", "email@example.com"),
            ("password", "mock_password"),
        ],
        "filter_query_parameters": [
            # ("search", "gncv://cli-mock/test.fastq.gz")
        ],
        "match_on": ["method", "scheme", "port", "path", "query"],
        "path_transformer": VCR.ensure_suffix(".yaml"),
        "before_record_request": [
            replace_gencove_url_vcr,
        ],
        "before_record_response": [
            filter_jwt,
            filter_volatile_dates,
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


MOCKED_UPLOADS = dict(
    meta=dict(next=None),
    results=[
        {
            "client_id": "clientid1",
            "fastq": {
                "r1": {
                    "upload": str(uuid4()),
                    "destination_path": "gncv://batch1/clientid1_R1.fastq.gz",
                },
                "r2": {
                    "upload": str(uuid4()),
                    "destination_path": "gncv://batch1/clientid1_R2.fastq.gz",
                },
            },
        },
        {
            "client_id": "clientid2",
            "fastq": {
                "r1": {
                    "upload": str(uuid4()),
                    "destination_path": "gncv://batch2/clientid2_R1.fastq.gz",
                }
            },
        },
    ],
)


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
    assert (
        res.output == "ERROR: Could not connect to the api server\nAborted!\n"
    )


def test_list_uploads(mocker):
    """Test list uploads being outputed to the shell."""
    runner = CliRunner()
    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_get_sample_sheet = mocker.patch.object(
        APIClient,
        "get_sample_sheet",
        return_value=SampleSheet(**MOCKED_UPLOADS),
    )
    res = runner.invoke(
        list_uploads, ["--email", "foo@bar.com", "--password", "123"]
    )
    assert res.exit_code == 0
    mocked_login.assert_called_once()
    mocked_get_sample_sheet.assert_called_once()

    output_line = io.BytesIO()
    sys.stdout = output_line
    echo(
        "\t".join(
            [
                MOCKED_UPLOADS["results"][0]["client_id"],
                MOCKED_UPLOADS["results"][0]["fastq"]["r1"]["upload"],
                MOCKED_UPLOADS["results"][0]["fastq"]["r1"][
                    "destination_path"
                ],
                MOCKED_UPLOADS["results"][0]["fastq"]["r2"]["upload"],
                MOCKED_UPLOADS["results"][0]["fastq"]["r2"][
                    "destination_path"
                ],
            ]
        )
    )
    echo(
        "\t".join(
            [
                MOCKED_UPLOADS["results"][1]["client_id"],
                MOCKED_UPLOADS["results"][1]["fastq"]["r1"]["upload"],
                MOCKED_UPLOADS["results"][1]["fastq"]["r1"][
                    "destination_path"
                ],
            ]
        )
    )
    assert output_line.getvalue() == res.output.encode()
