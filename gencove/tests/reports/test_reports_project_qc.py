"""Test reports project-qc command."""

# pylint: disable=wrong-import-order, import-error
import operator
import os

from click.testing import CliRunner

from gencove.client import APIClient  # noqa: I100
from gencove.command.reports.cli import project_qc
from gencove.tests.decorators import assert_authorization
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


@pytest.mark.vcr
@assert_authorization
def test_project_qc__success(
    credentials, mocker, project_id, recording, vcr, using_api_key
):
    """Test QC report success case"""
    runner = CliRunner()
    if not recording:
        project_qc_response = get_vcr_response(
            "/api/v2/project-qc-report/", vcr, operator.contains, just_body=False
        )
        mocked_project_qc = mocker.patch.object(
            APIClient,
            "get_project_qc_report",
            return_value=project_qc_response,
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
    assert "Saved project QC report CSV" in res.output
