"""Test project's create sample manifest command."""
import csv

import operator
import tempfile
import uuid

from click.testing import CliRunner

from gencove.client import APIClient  # noqa: I100
from gencove.command.projects.cli import get_sample_manifests
from gencove.tests.decorators import assert_authorization, assert_no_requests
from gencove.tests.filters import (
    filter_jwt,
    replace_gencove_url_vcr,
    filter_aws_headers,
)
from gencove.tests.projects.vcr.filters import (
    filter_project_sample_manifest_request,
    filter_get_project_sample_manifest_response,
    filter_get_sample_manifest_files_request,
    filter_get_sample_manifest_files_response,
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
        "filter_headers": ["Authorization", "Content-Length", "User-Agent", "ETag"],
        "filter_post_data_parameters": [
            ("email", "email@example.com"),
            ("password", "mock_password"),
        ],
        "match_on": ["method", "scheme", "port", "path", "query"],
        "path_transformer": VCR.ensure_suffix(".yaml"),
        "before_record_request": [
            replace_gencove_url_vcr,
            filter_project_sample_manifest_request,
            filter_get_sample_manifest_files_request,
        ],
        "before_record_response": [
            filter_jwt,
            filter_aws_headers,
            filter_volatile_dates,
            filter_get_project_sample_manifest_response,
            filter_get_sample_manifest_files_response,
        ],
    }


@pytest.mark.vcr
@assert_authorization
def test_get_sample_manifests__success(
    credentials,
    mocker,
    project_id_sample_manifest,
    recording,
    vcr,
):
    runner = CliRunner()
    if not recording:
        get_sample_manifest_response = get_vcr_response(
            "/api/v2/project-sample-manifests/", vcr, operator.contains
        )
        mocked_create_sample_manifest = mocker.patch.object(
            APIClient,
            "get_sample_manifests",
            return_value={},
        )
    with tempfile.TemporaryDirectory() as tempdir:
        res = runner.invoke(
            get_sample_manifests,
            [
                project_id_sample_manifest,
                tempdir,
                *credentials,
            ],
        )
    assert res.exit_code == 0
    if not recording:
        mocked_create_sample_manifest.assert_called_once()
