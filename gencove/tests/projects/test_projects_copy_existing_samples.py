"""Test copy existing project samples command."""

# pylint: disable=wrong-import-order, import-error
import operator
from unittest import mock
from uuid import uuid4

from click.testing import CliRunner

from gencove.client import APIClient, APIClientError
from gencove.command.projects.cli import copy_existing_project_samples
from gencove.constants import IMPORT_BATCH_SIZE
from gencove.models import (
    CopyExistingSamplesModel,
    SampleCopy,
)
from gencove.tests.decorators import assert_authorization, assert_no_requests
from gencove.tests.filters import filter_jwt, replace_gencove_url_vcr
from gencove.tests.projects.vcr.filters import (
    filter_copy_existing_samples_request,
    filter_copy_existing_samples_response,
    filter_get_project_samples_request,
    filter_get_project_samples_response,
)
from gencove.tests.utils import MOCK_UUID, get_vcr_response
from gencove.utils import batchify

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
            filter_get_project_samples_request,
            filter_copy_existing_samples_request,
        ],
        "before_record_response": [
            filter_jwt,
            filter_get_project_samples_response,
            filter_copy_existing_samples_response,
        ],
    }


@assert_no_requests
def test_copy_existing_project_samples__bad_project_id(mocker, credentials):
    """Test copy existing project samples failure when non-uuid string is used as
    project id.
    """
    runner = CliRunner()

    mocked_copy_existing_samples = mocker.patch.object(
        APIClient,
        "copy_existing_samples",
    )

    res = runner.invoke(
        copy_existing_project_samples,
        [
            "1111111",
            "--source-sample-ids",
            f"{str(uuid4())},{str(uuid4())}",
            *credentials,
        ],
    )

    assert res.exit_code == 1
    mocked_copy_existing_samples.assert_not_called()
    assert "Project ID is not valid" in res.output


@assert_no_requests
def test_copy_existing_project_samples__bad_sample_ids(mocker, credentials):
    """Test copy existing project samples failure when sample_ids are bad."""
    runner = CliRunner()

    mocked_copy_existing_samples = mocker.patch.object(
        APIClient,
        "copy_existing_samples",
    )

    res = runner.invoke(
        copy_existing_project_samples,
        [
            str(uuid4()),
            "--source-sample-ids",
            "1111111,2222222",
            *credentials,
        ],
    )

    assert res.exit_code == 1
    mocked_copy_existing_samples.assert_not_called()
    assert "Not all source sample IDs are valid" in res.output


@pytest.mark.default_cassette("jwt-create.yaml")
@pytest.mark.vcr
@assert_authorization
def test_copy_existing_project_samples__bad_source_project_id(mocker, credentials):
    """Test copy existing project samples failure when non-uuid string is used as
    source project id.
    """
    runner = CliRunner()

    mocked_copy_existing_samples = mocker.patch.object(
        APIClient,
        "copy_existing_samples",
    )

    res = runner.invoke(
        copy_existing_project_samples,
        [
            str(uuid4()),
            "--source-project-id",
            "1111111",
            *credentials,
        ],
    )

    assert res.exit_code == 1
    mocked_copy_existing_samples.assert_not_called()
    print(res.output)
    assert "Source project ID is not valid" in res.output


@pytest.mark.default_cassette("jwt-create.yaml")
@pytest.mark.vcr
@assert_authorization
def test_copy_existing_project_samples__same_project_id(mocker, credentials):
    """Test copy existing project samples failure when same project id is used
    as source and destination.
    """
    runner = CliRunner()

    mocked_copy_existing_samples = mocker.patch.object(
        APIClient,
        "copy_existing_samples",
    )

    project_id = str(uuid4())
    res = runner.invoke(
        copy_existing_project_samples,
        [
            project_id,
            "--source-project-id",
            project_id,
            *credentials,
        ],
    )

    assert res.exit_code == 1
    mocked_copy_existing_samples.assert_not_called()
    print(res.output)
    assert "Source and destination project must be different" in res.output


@pytest.mark.default_cassette("jwt-create.yaml")
@pytest.mark.vcr
@assert_authorization
def test_copy_existing_project_samples__both_sample_ids_and_source_project_id(
    mocker, credentials
):
    """Test copy existing project samples failure when both sample ids and
    source project id are given.
    """
    runner = CliRunner()

    mocked_copy_existing_samples = mocker.patch.object(
        APIClient,
        "copy_existing_samples",
    )

    res = runner.invoke(
        copy_existing_project_samples,
        [
            str(uuid4()),
            "--source-project-id",
            str(uuid4()),
            "--source-sample-ids",
            str(uuid4()),
            *credentials,
        ],
    )

    assert res.exit_code == 1
    mocked_copy_existing_samples.assert_not_called()
    print(res.output)
    assert "Either --source-project-id or --sample-ids" in res.output


@pytest.mark.vcr
@assert_authorization
def test_copy_existing_project_samples__server_rejects(
    mocker, credentials, project_id, recording, vcr
):
    """Test copy existing project samples failure when the validation
    fails on server.
    """
    runner = CliRunner()

    if not recording:
        # Mock copy_existing_samples only if using the cassettes, since we
        # mock the return value.
        project_samples_copy_response = get_vcr_response(
            "/api/v2/project-samples-copy/",
            vcr,
            operator.contains,
            just_body=False,
        )
        mocked_copy_existing_samples = mocker.patch.object(
            APIClient,
            "copy_existing_samples",
            side_effect=APIClientError(
                message=project_samples_copy_response["body"]["string"],
                status_code=project_samples_copy_response["status"]["code"],
            ),
        )

    res = runner.invoke(
        copy_existing_project_samples,
        [
            project_id,
            "--source-sample-ids",
            MOCK_UUID,
            *credentials,
        ],
    )
    assert res.exit_code == 1
    if not recording:
        mocked_copy_existing_samples.assert_called_once()
    assert "There was an error copying" in res.output


@pytest.mark.vcr
@assert_authorization
def test_copy_existing_project_samples__success(
    mocker, credentials, project_id_copy, sample_id_copy_existing, recording, vcr
):  # pylint: disable=too-many-arguments
    """Test copy existing project samples success."""
    runner = CliRunner()

    if not recording:
        # Mock copy_existing_samples only if using the cassettes, since we
        # mock the return value.
        project_samples_copy_response = get_vcr_response(
            "/api/v2/project-samples-copy/", vcr, operator.contains
        )
        mocked_copy_existing_samples = mocker.patch.object(
            APIClient,
            "copy_existing_samples",
            return_value=CopyExistingSamplesModel(**project_samples_copy_response),
        )

    res = runner.invoke(
        copy_existing_project_samples,
        [
            project_id_copy,
            "--source-sample-ids",
            sample_id_copy_existing,
            *credentials,
        ],
    )
    assert res.exit_code == 0
    if not recording:
        mocked_copy_existing_samples.assert_called_once()
    assert "Number of samples copied into the project" in res.output


@pytest.mark.default_cassette("jwt-create.yaml")
@pytest.mark.vcr
@assert_authorization
def test_copy_existing_project_samples__batch_size(
    mocker, credentials, project_id, recording, vcr  # pylint: disable=unused-argument
):  # pylint: disable=too-many-arguments
    """Test copy existing project samples confirm batch size."""
    runner = CliRunner()

    sample_ids = [str(uuid4()) for _ in range(IMPORT_BATCH_SIZE * 2 + 1)]

    mocked_copy_existing_samples = mocker.patch.object(
        APIClient,
        "copy_existing_samples",
        return_value=CopyExistingSamplesModel(
            project_id=project_id,
            samples=[SampleCopy(sample_id=sample_id) for sample_id in sample_ids],
        ),
    )

    res = runner.invoke(
        copy_existing_project_samples,
        [
            project_id,
            "--source-sample-ids",
            ",".join(sample_ids),
            *credentials,
        ],
    )
    assert res.exit_code == 0
    assert mocked_copy_existing_samples.call_count == 3
    mocked_copy_existing_samples.assert_has_calls(
        [
            mock.call(project_id, samples_batch)
            for samples_batch in batchify(sample_ids, IMPORT_BATCH_SIZE)
        ]
    )
    assert "Number of samples copied into the project" in res.output
