"""Test reports monthly-usage command."""

# pylint: disable=wrong-import-order, import-error
import operator
import os

from click.testing import CliRunner

from gencove.client import APIClient, APIClientError  # noqa: I100
from gencove.command.reports.cli import monthly_usage
from gencove.tests.decorators import assert_authorization
from gencove.tests.filters import (
    filter_aws_headers,
    filter_jwt,
    replace_gencove_url_vcr,
)
from gencove.tests.reports.vcr.filters import (
    filter_monthly_usage_report_request,
    filter_report_response_body,
    filter_report_response_filename,
)
from gencove.tests.upload.vcr.filters import filter_volatile_dates
from gencove.tests.utils import get_response_from_vcr_dict, get_vcr_response

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
            filter_monthly_usage_report_request,
        ],
        "before_record_response": [
            filter_jwt,
            filter_aws_headers,
            filter_volatile_dates,
            filter_report_response_body,
            filter_report_response_filename,
        ],
    }


@pytest.mark.vcr
@assert_authorization
def test_monthly_usage__success(  # pylint: disable=too-many-arguments,unused-argument
    credentials, mocker, recording, vcr
):
    """Test monthly usage report success case"""
    runner = CliRunner()
    if not recording:
        monthly_usage_dict = get_vcr_response(
            "/api/v2/organization-monthly-usage-report/",
            vcr,
            operator.contains,
            just_body=False,
        )
        response = get_response_from_vcr_dict(monthly_usage_dict)

        # Need to reconstruct the raw response
        mocked_monthly_usage = mocker.patch.object(
            APIClient,
            "get_organization_monthly_usage_report",
            return_value=response,
        )
    with runner.isolated_filesystem():
        os.mkdir("tempdir")
        res = runner.invoke(
            monthly_usage,
            [
                *credentials,
            ],
        )

    assert res.exit_code == 0
    if not recording:
        mocked_monthly_usage.assert_called_once()
    assert "Saved organization monthly usage report CSV" in res.output


@pytest.mark.vcr
@assert_authorization
def test_monthly_usage__success_dates(
    credentials, mocker, recording, vcr
):  # pylint: disable=too-many-arguments,too-many-locals,unused-argument
    """Test monthly usage report success case with requested dates"""
    runner = CliRunner()
    if not recording:
        monthly_usage_dict = get_vcr_response(
            "/api/v2/organization-monthly-usage-report/",
            vcr,
            operator.contains,
            just_body=False,
        )
        response = get_response_from_vcr_dict(monthly_usage_dict)

        # Need to reconstruct the raw response
        mocked_monthly_usage = mocker.patch.object(
            APIClient,
            "get_organization_monthly_usage_report",
            return_value=response,
        )
    with runner.isolated_filesystem():
        os.mkdir("tempdir")
        outfile = "tempdir/test.csv"
        res = runner.invoke(
            monthly_usage,
            [
                "--output-filename",
                f"{outfile}",
                "--from",
                "2021-09",
                "--to",
                "2021-10",
                *credentials,
            ],
        )

        with open(outfile, "r", encoding="utf-8") as fileobj:
            contents = fileobj.readlines()

    assert res.exit_code == 0
    if not recording:
        mocked_monthly_usage.assert_called_once()
    assert "Saved organization monthly usage report CSV" in res.output

    # Confirm columns are as expected
    columns_row = contents[0]
    columns = columns_row.strip().split(",")
    assert "year" in columns
    assert "month" in columns
    assert "succeeded_samples" in columns
    assert "failed_samples" in columns

    # should be two months of data + headers
    assert len(contents) == 3


@pytest.mark.vcr
@assert_authorization
def test_monthly_usage__bad_date(  # pylint: disable=too-many-arguments,unused-argument
    credentials, mocker, recording, vcr
):
    """Test monthly usage report with bad date value"""
    runner = CliRunner()
    if not recording:
        monthly_usage_dict = get_vcr_response(
            "/api/v2/organization-monthly-usage-report/",
            vcr,
            operator.contains,
            just_body=False,
        )
        response = get_response_from_vcr_dict(monthly_usage_dict)

        # Need to reconstruct the raw response
        mocked_monthly_usage = mocker.patch.object(
            APIClient,
            "get_organization_monthly_usage_report",
            side_effect=APIClientError(
                message=response.content,
                status_code=response.status_code,
            ),
            return_value=response,
        )

    with runner.isolated_filesystem():
        os.mkdir("tempdir")
        # invoke without --to param
        res = runner.invoke(
            monthly_usage,
            [
                "--from",
                "2023-01",
                *credentials,
            ],
        )

    assert res.exit_code == 0
    if not recording:
        mocked_monthly_usage.assert_called_once()
    assert "There was an error retrieving the monthly usage report" in res.output
    assert (
        "Must provide both 'from' and 'to' query parameters, or neither" in res.output
    )
