"""Test sample manifest get command."""

# pylint: disable=wrong-import-order, import-error
import operator
import os
import uuid

from click.testing import CliRunner

from gencove.client import APIClient, APIClientError  # noqa: I100
from gencove.command.sample_manifests.cli import get_sample_manifest
from gencove.models import SampleManifest
from gencove.tests.decorators import assert_authorization, assert_no_requests
from gencove.tests.filters import (
    filter_aws_headers,
    filter_jwt,
    replace_gencove_url_vcr,
)
from gencove.tests.projects.vcr.filters import (
    filter_get_sample_manifest_files_response,
    filter_sample_manifests_request,
)
from gencove.tests.sample_manifests.vcr.filters import (
    filter_get_sample_manifest_response,
    filter_sample_manifest_request,
)
from gencove.tests.upload.vcr.filters import filter_volatile_dates
from gencove.tests.utils import get_vcr_response

import pytest

from vcr import VCR


@pytest.fixture(scope="module")
def vcr_config():
    """VCR configuration."""
    return {
        "cassette_library_dir": "gencove/tests/sample_manifests/vcr",
        "filter_headers": ["Authorization", "Content-Length", "User-Agent", "ETag"],
        "filter_post_data_parameters": [
            ("email", "email@example.com"),
            ("password", "mock_password"),
        ],
        "match_on": ["method", "scheme", "port", "path", "query"],
        "path_transformer": VCR.ensure_suffix(".yaml"),
        "before_record_request": [
            replace_gencove_url_vcr,
            filter_sample_manifests_request,
            filter_sample_manifest_request,
        ],
        "before_record_response": [
            filter_jwt,
            filter_aws_headers,
            filter_volatile_dates,
            filter_get_sample_manifest_files_response,
            filter_get_sample_manifest_response,
        ],
    }


@pytest.mark.vcr
@assert_authorization
def test_get_sample_manifest__not_owned(
    credentials,
    mocker,
    recording,
    vcr,
):
    """Test sample manifest not owned case"""
    runner = CliRunner()
    if not recording:
        get_sample_manifest_response = get_vcr_response(
            "/api/v2/sample-manifests/", vcr, operator.contains
        )
        mocked_get_sample_manifest = mocker.patch.object(
            APIClient,
            "get_sample_manifest",
            side_effect=APIClientError(
                message="Not found",
                status_code=400,
            ),
            return_value=get_sample_manifest_response,
        )
    with runner.isolated_filesystem():
        os.mkdir("tempdir")
        res = runner.invoke(
            get_sample_manifest,
            [
                str(uuid.uuid4()),
                "tempdir",
                *credentials,
            ],
        )
    assert res.exit_code == 0
    if not recording:
        mocked_get_sample_manifest.assert_called_once()
    assert "Not found" in res.output


@pytest.mark.vcr
@assert_authorization
def test_get_sample_manifest__success(
    credentials,
    mocker,
    sample_manifest_id,
    recording,
    vcr,
):
    """Test sample manifest success case"""
    runner = CliRunner()
    if not recording:
        get_sample_manifest_response = get_vcr_response(
            "/api/v2/sample-manifests/", vcr, operator.contains
        )
        mocked_get_sample_manifest = mocker.patch.object(
            APIClient,
            "get_sample_manifest",
            return_value=SampleManifest(**get_sample_manifest_response),
        )
    with runner.isolated_filesystem():
        os.mkdir("tempdir")
        res = runner.invoke(
            get_sample_manifest,
            [
                sample_manifest_id,
                "tempdir",
                *credentials,
            ],
        )
    assert res.exit_code == 0
    if not recording:
        mocked_get_sample_manifest.assert_called_once()
    assert "Downloading manifest" in res.output


@assert_no_requests
def test_get_sample_manifests__bad_manifest_id(credentials, mocker):
    """Test manifest retrieve failure when non-uuid string is used as project
    id.
    """
    runner = CliRunner()
    mocked_get_sample_manifest = mocker.patch.object(
        APIClient,
        "get_sample_manifest",
    )
    with runner.isolated_filesystem():
        os.mkdir("tempdir")
        res = runner.invoke(
            get_sample_manifest,
            [
                "1111111",
                "tempdir",
                *credentials,
            ],
        )
    assert res.exit_code == 1
    mocked_get_sample_manifest.assert_not_called()
    assert "manifest_id is not valid" in res.output


@assert_no_requests
def test_get_sample_manifests__bad_destination(credentials, mocker):
    """Test manifest retrieve failure when non-uuid string is used as project
    id.
    """
    runner = CliRunner()
    mocked_get_sample_manifest = mocker.patch.object(
        APIClient,
        "get_sample_manifest",
    )
    res = runner.invoke(
        get_sample_manifest,
        [
            str(uuid.uuid4()),
            "foo",
            *credentials,
        ],
    )
    assert res.exit_code == 1
    mocked_get_sample_manifest.assert_not_called()
    assert "destination is not a directory that exists" in res.output
