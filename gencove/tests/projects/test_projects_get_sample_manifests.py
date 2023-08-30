"""Test project's get sample manifest command."""

# pylint: disable=wrong-import-order, import-error
import operator
import os
import uuid

from click.testing import CliRunner

from gencove.client import APIClient, APIClientError  # noqa: I100
from gencove.command.projects.cli import get_sample_manifests
from gencove.models import SampleManifest
from gencove.tests.decorators import assert_authorization, assert_no_requests
from gencove.tests.filters import (
    filter_aws_headers,
    filter_jwt,
    replace_gencove_url_vcr,
)
from gencove.tests.projects.vcr.filters import (
    filter_get_project_sample_manifests_response,
    filter_get_sample_manifest_files_response,
    filter_project_sample_manifest_request,
    filter_sample_manifests_request,
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
            filter_sample_manifests_request,
        ],
        "before_record_response": [
            filter_jwt,
            filter_aws_headers,
            filter_volatile_dates,
            filter_get_project_sample_manifests_response,
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
):  # pylint: disable=unused-argument
    """Test get sample manifests success case"""
    runner = CliRunner()
    if not recording:
        get_sample_manifest_response = get_vcr_response(
            "/api/v2/project-sample-manifests/", vcr, operator.contains
        )
        mocker.patch(
            "gencove.command.projects.get_sample_manifests.main.download_file",
        )
        mocked_get_sample_manifests = mocker.patch.object(
            APIClient,
            "get_sample_manifests",
            return_value=[SampleManifest(**x) for x in get_sample_manifest_response],
        )

    with runner.isolated_filesystem():
        os.mkdir("test_dir")
        res = runner.invoke(
            get_sample_manifests,
            [
                project_id_sample_manifest,
                "test_dir",
                *credentials,
            ],
        )
    assert res.exit_code == 0
    if not recording:
        mocked_get_sample_manifests.assert_called_once()
    assert "Downloading sample manifest" in res.output


@pytest.mark.vcr
@assert_authorization
def test_get_sample_manifests__empty(
    credentials,
    mocker,
    project_id,  # project without any manifests
    recording,
    vcr,
):
    """Get sample manifests empty case"""
    runner = CliRunner()
    if not recording:
        get_sample_manifest_response = get_vcr_response(
            "/api/v2/project-sample-manifests/", vcr, operator.contains
        )
        mocked_get_sample_manifests = mocker.patch.object(
            APIClient,
            "get_sample_manifests",
            return_value=get_sample_manifest_response,
        )
        mocker.patch(
            "gencove.command.projects.get_sample_manifests.main.download_file",
        )
    with runner.isolated_filesystem():
        os.mkdir("test_dir")
        res = runner.invoke(
            get_sample_manifests,
            [
                project_id,
                "test_dir",
                *credentials,
            ],
        )
    assert res.exit_code == 0
    if not recording:
        mocked_get_sample_manifests.assert_called_once()
    assert res.output == ""


@pytest.mark.vcr
@assert_authorization
def test_get_sample_manifests__not_owned_project(
    credentials, recording, mocker, vcr
):  # pylint: disable=unused-argument
    """Get sample manifests project not owned case"""
    runner = CliRunner()
    mocker.patch.object(
        APIClient,
        "get_sample_manifests",
        side_effect=APIClientError(
            message="Project does not exist or you do not have privileges to access it",
            status_code=400,
        ),
    )
    with runner.isolated_filesystem():
        os.mkdir("test_dir")
        res = runner.invoke(
            get_sample_manifests,
            [
                str(uuid.uuid4()),
                "test_dir",
                *credentials,
            ],
        )
    assert res.exit_code == 0
    assert (
        "Project does not exist or you do not have privileges to access it"
        in res.output
    )


@assert_no_requests
def test_get_sample_manifests__bad_project_id(credentials, mocker):
    """Test manifest retrieve failure when non-uuid string is used as project
    id.
    """
    runner = CliRunner()
    mocked_get_sample_manifests = mocker.patch.object(
        APIClient,
        "get_sample_manifests",
    )
    with runner.isolated_filesystem():
        os.mkdir("test_dir")
        res = runner.invoke(
            get_sample_manifests,
            [
                "1111111",
                "test_dir",
                *credentials,
            ],
        )
    assert res.exit_code == 1
    mocked_get_sample_manifests.assert_not_called()
    assert "Project ID is not valid" in res.output


@assert_no_requests
def test_get_sample_manifests__bad_destination(credentials, mocker):
    """Test manifest retrieve failure when bad destination is supplied
    id.
    """
    runner = CliRunner()
    mocked_get_sample_manifests = mocker.patch.object(
        APIClient,
        "get_sample_manifests",
    )
    with runner.isolated_filesystem():
        res = runner.invoke(
            get_sample_manifests,
            [
                str(uuid.uuid4()),
                "bad_dir",
                *credentials,
            ],
        )
    assert res.exit_code == 1
    mocked_get_sample_manifests.assert_not_called()
    assert "is not a directory that exists" in res.output
