"""Test project's batches create command."""
# pylint: disable=wrong-import-order, import-error
import io
import operator
import sys
from uuid import uuid4

from click import echo
from click.testing import CliRunner

from gencove.client import APIClient, APIClientError  # noqa: I100
from gencove.command.projects.cli import create_project_batch
from gencove.models import ProjectBatches
from gencove.tests.decorators import assert_authorization
from gencove.tests.filters import filter_jwt, replace_gencove_url_vcr
from gencove.tests.projects.vcr.filters import (
    filter_project_batches_request,
    filter_project_batches_response,
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
            filter_project_batches_request,
        ],
        "before_record_response": [
            filter_jwt,
            filter_volatile_dates,
            filter_project_batches_response,
        ],
    }


@pytest.mark.default_cassette("jwt-create.yaml")
@pytest.mark.vcr
@assert_authorization
def test_create_project_batches__missing_batch_type(credentials, mocker):
    """Test batch creation failure when batch type is not sent."""
    runner = CliRunner()
    mocked_create_project_batch = mocker.patch.object(APIClient, "create_project_batch")
    res = runner.invoke(
        create_project_batch,
        [
            str(uuid4()),
            *credentials,
            "--batch-name",
            "foo bar",
        ],
    )
    assert res.exit_code == 1
    mocked_create_project_batch.assert_not_called()
    assert "You must provide value for --batch-type" in res.output


@pytest.mark.default_cassette("jwt-create.yaml")
@pytest.mark.vcr
@assert_authorization
def test_create_project_batches__missing_batch_name(credentials, mocker):
    """Test batch creation failure when batch name is not sent."""
    runner = CliRunner()
    mocked_create_project_batch = mocker.patch.object(APIClient, "create_project_batch")
    res = runner.invoke(
        create_project_batch,
        [
            str(uuid4()),
            *credentials,
            "--batch-type",
            "hd777k",
        ],
    )
    assert res.exit_code == 1
    mocked_create_project_batch.assert_not_called()
    assert "You must provide value for --batch-name" in res.output


@pytest.mark.default_cassette("jwt-create.yaml")
@pytest.mark.vcr
@assert_authorization
def test_create_project_batches__bad_project_id(credentials, mocker):
    """Test batch creation failure when non-uuid string is used as project
    id.
    """
    runner = CliRunner()
    mocked_create_project_batch = mocker.patch.object(
        APIClient,
        "create_project_batch",
    )
    res = runner.invoke(
        create_project_batch,
        [
            "1111111",
            *credentials,
            "--batch-type",
            "hd777k",
            "--batch-name",
            "foo bar",
        ],
    )
    assert res.exit_code == 1
    mocked_create_project_batch.assert_not_called()
    assert "Project ID is not valid" in res.output


@pytest.mark.default_cassette("jwt-create.yaml")
@pytest.mark.vcr
@assert_authorization
def test_create_project_batches__not_owned_project(credentials, mocker):
    """Test batch creation failure when project is not owned."""
    runner = CliRunner()
    mocked_create_project_batch = mocker.patch.object(
        APIClient,
        "create_project_batch",
        side_effect=APIClientError(message="", status_code=403),
    )

    res = runner.invoke(
        create_project_batch,
        [
            str(uuid4()),
            *credentials,
            "--batch-type",
            "hd777k",
            "--batch-name",
            "foo bar",
        ],
    )
    assert res.exit_code == 1
    mocked_create_project_batch.assert_called_once()
    assert "You do not have the sufficient permission" in res.output


@pytest.mark.default_cassette("jwt-create.yaml")
@pytest.mark.vcr
@assert_authorization
def test_create_project_batches__duplicate_client_ids(credentials, mocker):
    """Test batch creation failure when there are samples that share same
    client id.
    """
    runner = CliRunner()
    mocked_create_project_batch = mocker.patch.object(
        APIClient,
        "create_project_batch",
        side_effect=APIClientError(message="", status_code=400),
    )

    res = runner.invoke(
        create_project_batch,
        [
            str(uuid4()),
            *credentials,
            "--batch-type",
            "hd777k",
            "--batch-name",
            "foo bar",
        ],
    )
    assert res.exit_code == 0
    mocked_create_project_batch.assert_called_once()
    assert "There was an error creating project batches" in res.output


@pytest.mark.vcr
@assert_authorization
def test_create_project_batches__success__with_sample_ids(
    batch_name,
    batch_type,
    credentials,
    mocker,
    project_id_batches,
    recording,
    sample_id_batches,
    vcr,
):  # pylint: disable=too-many-arguments
    """Test batch creation success when when sample ids are explicitly sent."""
    runner = CliRunner()
    if not recording:
        # Mock create_project_batch only if using the cassettes, since we
        # mock the return value.
        create_project_batch_response = get_vcr_response(
            "/api/v2/project-batches/", vcr, operator.contains
        )
        mocked_create_project_batch = mocker.patch.object(
            APIClient,
            "create_project_batch",
            return_value=ProjectBatches(**create_project_batch_response),
        )
    res = runner.invoke(
        create_project_batch,
        [
            project_id_batches,
            *credentials,
            "--batch-type",
            batch_type,
            "--batch-name",
            batch_name,
            "--sample-ids",
            sample_id_batches,
        ],
    )
    assert res.exit_code == 0
    if not recording:
        mocked_create_project_batch.assert_called_once()

        output_line = io.BytesIO()
        sys.stdout = output_line
        for response in ProjectBatches(**create_project_batch_response).results:
            echo(
                "\t".join(
                    [
                        str(response.id),
                        response.last_status.created.isoformat(),
                        response.last_status.status,
                        response.batch_type,
                        response.name,
                    ]
                )
            )
        assert output_line.getvalue() == res.output.encode()


@pytest.mark.vcr
@assert_authorization
def test_create_project_batches__success__without_sample_ids(
    batch_name,
    batch_type,
    credentials,
    mocker,
    project_id_batches,
    recording,
    vcr,
):  # pylint: disable=too-many-arguments
    """Test batch creation success when when sample ids are not explicitly
    sent.
    """
    runner = CliRunner()
    if not recording:
        # Mock create_project_batch only if using the cassettes, since we
        # mock the return value.
        create_project_batch_response = get_vcr_response(
            "/api/v2/project-batches/", vcr, operator.contains
        )
        mocked_create_project_batch = mocker.patch.object(
            APIClient,
            "create_project_batch",
            return_value=ProjectBatches(**create_project_batch_response),
        )
    res = runner.invoke(
        create_project_batch,
        [
            project_id_batches,
            *credentials,
            "--batch-type",
            batch_type,
            "--batch-name",
            batch_name,
        ],
    )
    assert res.exit_code == 0
    if not recording:
        mocked_create_project_batch.assert_called_once()

        output_line = io.BytesIO()
        sys.stdout = output_line
        for response in ProjectBatches(**create_project_batch_response).results:
            echo(
                "\t".join(
                    [
                        str(response.id),
                        response.last_status.created.isoformat(),
                        response.last_status.status,
                        response.batch_type,
                        response.name,
                    ]
                )
            )
        assert output_line.getvalue() == res.output.encode()
