"""Test reports project-qc command."""

# pylint: disable=wrong-import-order, import-error
import operator
import os

from click.testing import CliRunner

from requests import Response

from gencove.client import APIClient, APIClientError  # noqa: I100
from gencove.command.reports.cli import project_qc
from gencove.tests.filters import (
    filter_aws_headers,
    filter_jwt,
    replace_gencove_url_vcr,
)
from gencove.tests.reports.vcr.filters import (
    filter_project_qc_report_request,
    filter_project_qc_report_response_body,
    filter_project_qc_report_response_filename,
)
from gencove.tests.upload.vcr.filters import filter_volatile_dates
from gencove.tests.utils import get_vcr_response

import pytest

from vcr import VCR


@pytest.fixture(scope="module")
def vcr_config():
    """VCR configuration."""
    return {
        "cassette_library_dir": "gencove/tests/reports/vcr",
        "filter_headers": ["Authorization", "Content-Length", "User-Agent", "ETag"],
        "filter_post_data_parameters": [
            ("email", "email@example.com"),
            ("password", "mock_password"),
        ],
        "match_on": ["method", "scheme", "port", "path", "query"],
        "path_transformer": VCR.ensure_suffix(".yaml"),
        "before_record_request": [
            replace_gencove_url_vcr,
            filter_project_qc_report_request,
        ],
        "before_record_response": [
            filter_jwt,
            filter_aws_headers,
            filter_volatile_dates,
            filter_project_qc_report_response_body,
            filter_project_qc_report_response_filename,
        ],
    }


def get_response_from_vcr_dict(vcr_dict: dict) -> Response:
    """Create Response object from get_vcr_response return value"""
    response = Response()
    response.status_code = vcr_dict["status"]["code"]
    response.headers = vcr_dict["headers"]
    content_disposition = response.headers.get("Content-Disposition")
    if content_disposition:
        response.headers["content-disposition"] = content_disposition[0]
    response._content = vcr_dict["body"]["string"]  # pylint: disable=protected-access
    return response


@pytest.mark.vcr
def test_project_qc__not_owned(
    credentials,
    mocker,
    recording,
    vcr,
):
    """Test project qc report not owned case"""
    runner = CliRunner()
    if not recording:
        project_qc_dict = get_vcr_response(
            "/api/v2/project-qc-report/", vcr, operator.contains, just_body=False
        )
        response = get_response_from_vcr_dict(project_qc_dict)

        mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
        mocked_project_qc = mocker.patch.object(
            APIClient,
            "get_project_qc_report",
            side_effect=APIClientError(message="", status_code=response.status_code),
            return_value=response,
        )
    with runner.isolated_filesystem():
        os.mkdir("tempdir")
        res = runner.invoke(
            project_qc,
            [
                "11111111-1111-1111-1111-111111111111",
                *credentials,
            ],
        )

    assert res.exit_code == 0
    if not recording:
        mocked_project_qc.assert_called_once()
        mocked_login.assert_called_once()
    assert "does not exist or you do not have access" in res.output


@pytest.mark.vcr
def test_project_qc__success(  # pylint: disable=too-many-arguments
    credentials, mocker, project_id, recording, vcr, using_api_key
):
    """Test QC report success case"""
    runner = CliRunner()
    if not recording:
        project_qc_dict = get_vcr_response(
            "/api/v2/project-qc-report/", vcr, operator.contains, just_body=False
        )
        response = get_response_from_vcr_dict(project_qc_dict)

        # Need to reconstruct the raw response
        mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
        mocked_project_qc = mocker.patch.object(
            APIClient,
            "get_project_qc_report",
            return_value=response,
        )
    with runner.isolated_filesystem():
        os.mkdir("tempdir")
        res = runner.invoke(
            project_qc,
            [
                project_id,
                *credentials,
            ],
        )

    assert res.exit_code == 0
    if not recording:
        mocked_project_qc.assert_called_once()
        mocked_login.assert_called_once()
    assert "Saved project QC report CSV" in res.output


@pytest.mark.vcr
def test_project_qc__success_columns(  # pylint: disable=too-many-arguments
    credentials, mocker, project_id, recording, vcr, using_api_key
):
    """Test QC report success case with requested coluns"""
    runner = CliRunner()
    if not recording:
        project_qc_dict = get_vcr_response(
            "/api/v2/project-qc-report/", vcr, operator.contains, just_body=False
        )
        response = get_response_from_vcr_dict(project_qc_dict)

        # Need to reconstruct the raw response
        mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
        mocked_project_qc = mocker.patch.object(
            APIClient,
            "get_project_qc_report",
            return_value=response,
        )
    with runner.isolated_filesystem():
        os.mkdir("tempdir")
        outfile = "tempdir/test.csv"
        res = runner.invoke(
            project_qc,
            [
                "--output-filename",
                "tempdir/test.csv",
                "--columns",
                "id,client_id",
                project_id,
                *credentials,
            ],
        )
        with open(outfile, "r") as f:
            contents = f.readlines()

    assert res.exit_code == 0
    if not recording:
        mocked_project_qc.assert_called_once()
        mocked_login.assert_called_once()
    assert "Saved project QC report CSV" in res.output

    # Confirm columns are as expected
    columns_row = contents[0]
    columns = columns_row.strip().split(",")
    assert len(columns) == 2
    assert columns[0] == "id"
    assert columns[1] == "client_id"


@pytest.mark.vcr
def test_project_qc__bad_columns(  # pylint: disable=too-many-arguments
    credentials, mocker, project_id, recording, vcr, using_api_key
):
    """Test QC report with bad column name passed to --columns"""
    runner = CliRunner()
    if not recording:
        project_qc_dict = get_vcr_response(
            "/api/v2/project-qc-report/", vcr, operator.contains, just_body=False
        )
        response = get_response_from_vcr_dict(project_qc_dict)

        # Need to reconstruct the raw response
        mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
        mocked_project_qc = mocker.patch.object(
            APIClient,
            "get_project_qc_report",
            side_effect=APIClientError(
                message="API Client Error: Bad Request",
                status_code=response.status_code,
            ),
            return_value=response,
        )

    with runner.isolated_filesystem():
        os.mkdir("tempdir")
        res = runner.invoke(
            project_qc,
            [
                "--columns",
                "id,invalid_column",
                project_id,
                *credentials,
            ],
        )

    assert res.exit_code == 0
    if not recording:
        mocked_project_qc.assert_called_once()
        mocked_login.assert_called_once()
    assert "There was an error retrieving the project QC report" in res.output
