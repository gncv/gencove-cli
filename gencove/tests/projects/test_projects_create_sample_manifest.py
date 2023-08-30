"""Test project's create sample manifest command."""

# pylint: disable=wrong-import-order, import-error
import csv
import operator
import tempfile
import uuid

from click.testing import CliRunner

from gencove.client import APIClient  # noqa: I100
from gencove.command.projects.cli import create_sample_manifest
from gencove.tests.decorators import assert_authorization, assert_no_requests
from gencove.tests.filters import filter_jwt, replace_gencove_url_vcr
from gencove.tests.projects.vcr.filters import (
    filter_project_sample_manifest_request,
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
            filter_project_sample_manifest_request,
        ],
        "before_record_response": [
            filter_jwt,
            filter_volatile_dates,
        ],
    }


@pytest.fixture(scope="function")
def dummy_valid_manifest_csv():
    """Valid manifest CSV file"""

    manifest_columns = [
        "Plate ID",
        "Well",
        "Unique sample identifier",
        "Buffer",
        "Concentration if known (ng/ul)",
        "Species",
        "Coverage",
    ]

    well_pattern_96 = [
        letter + str(num) for num in range(1, 13) for letter in "ABCDEFGH"
    ]
    with tempfile.NamedTemporaryFile(
        mode="w+", suffix=".csv", delete=False
    ) as tmp_file:
        writer = csv.writer(tmp_file)
        writer.writerow(manifest_columns)  # header
        writer.writerow(["", "A1", "client-id", "", "", "", ""])
        for well in well_pattern_96[1:]:
            writer.writerow(["", well, "", "", "", "", ""])
        tmp_file.seek(0)
    return tmp_file.name


@pytest.mark.vcr
@assert_authorization
def test_create_sample_manifest__success(
    credentials,
    mocker,
    project_id_sample_manifest,
    dummy_valid_manifest_csv,
    recording,
    vcr,
):  # pylint: disable=too-many-arguments,redefined-outer-name
    """Create sample manifest success case"""
    runner = CliRunner()
    if not recording:
        # Mock create_project only if using the cassettes, since we
        # mock the return value.
        create_sample_manifest_response = get_vcr_response(
            "/api/v2/project-sample-manifests/", vcr, operator.contains
        )
        mocked_create_sample_manifest = mocker.patch.object(
            APIClient,
            "create_sample_manifest",
            return_value=create_sample_manifest_response,
        )
    res = runner.invoke(
        create_sample_manifest,
        [
            project_id_sample_manifest,
            dummy_valid_manifest_csv,
            *credentials,
        ],
    )
    assert res.exit_code == 0
    if not recording:
        mocked_create_sample_manifest.assert_called_once()


@pytest.mark.vcr
@assert_authorization
def test_create_sample_manifest__not_owned_project(
    credentials,
    mocker,
    dummy_valid_manifest_csv,
    recording,
):  # pylint: disable=unused-argument,redefined-outer-name
    """Test project not owned case"""
    runner = CliRunner()
    res = runner.invoke(
        create_sample_manifest,
        [
            str(uuid.uuid4()),
            dummy_valid_manifest_csv,
            *credentials,
        ],
    )
    assert (
        "Project does not exist or you do not have privileges to access it"
        in res.output
    )


@assert_no_requests
def test_create_sample_manifest__bad_project_id(
    credentials, mocker, dummy_valid_manifest_csv
):  # pylint: disable=redefined-outer-name
    """Test manifest creation failure when non-uuid string is used as project
    id.
    """
    runner = CliRunner()
    mocked_create_sample_manifest = mocker.patch.object(
        APIClient,
        "create_sample_manifest",
    )
    res = runner.invoke(
        create_sample_manifest,
        [
            "1111111",
            dummy_valid_manifest_csv,
            *credentials,
        ],
    )
    assert res.exit_code == 1
    mocked_create_sample_manifest.assert_not_called()
    assert "Project ID is not valid" in res.output
