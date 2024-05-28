"""Test import existing project samples command."""

# pylint: disable=wrong-import-order, import-error
import operator
from unittest import mock
from uuid import uuid4

from click.testing import CliRunner

from gencove.client import APIClient, APIClientError
from gencove.command.projects.cli import import_existing_project_samples
from gencove.constants import IMPORT_BATCH_SIZE
from gencove.models import (
    ImportExistingSamplesModel,
    ProjectSamples,
    SampleImport,
)
from gencove.tests.decorators import assert_authorization, assert_no_requests
from gencove.tests.filters import filter_jwt, replace_gencove_url_vcr
from gencove.tests.projects.vcr.filters import (
    filter_get_project_samples_request,
    filter_get_project_samples_response,
    filter_import_existing_samples_request,
    filter_import_existing_samples_response,
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
            filter_import_existing_samples_request,
        ],
        "before_record_response": [
            filter_jwt,
            filter_get_project_samples_response,
            filter_import_existing_samples_response,
        ],
    }


@assert_no_requests
def test_import_existing_project_samples__bad_project_id(mocker, credentials):
    """Test import existing project samples failure when non-uuid string is used as
    project id.
    """
    runner = CliRunner()

    mocked_import_existing_samples = mocker.patch.object(
        APIClient,
        "import_existing_samples",
    )

    res = runner.invoke(
        import_existing_project_samples,
        [
            "1111111",
            "--sample-ids",
            f"{str(uuid4())},{str(uuid4())}",
            *credentials,
        ],
    )

    assert res.exit_code == 1
    mocked_import_existing_samples.assert_not_called()
    assert "Project ID is not valid" in res.output


@assert_no_requests
def test_import_existing_project_samples__bad_sample_ids(mocker, credentials):
    """Test import existing project samples failure when sample_ids are bad."""
    runner = CliRunner()

    mocked_import_existing_samples = mocker.patch.object(
        APIClient,
        "import_existing_samples",
    )

    res = runner.invoke(
        import_existing_project_samples,
        [
            str(uuid4()),
            "--sample-ids",
            "1111111,2222222",
            *credentials,
        ],
    )

    assert res.exit_code == 1
    mocked_import_existing_samples.assert_not_called()
    assert "Not all source sample IDs are valid" in res.output


@pytest.mark.default_cassette("jwt-create.yaml")
@pytest.mark.vcr
@assert_authorization
def test_import_existing_project_samples__bad_source_project_id(mocker, credentials):
    """Test import existing project samples failure when non-uuid string is used as
    source project id.
    """
    runner = CliRunner()

    mocked_import_existing_samples = mocker.patch.object(
        APIClient,
        "import_existing_samples",
    )

    res = runner.invoke(
        import_existing_project_samples,
        [
            str(uuid4()),
            "--source-project-id",
            "1111111",
            *credentials,
        ],
    )

    assert res.exit_code == 1
    mocked_import_existing_samples.assert_not_called()
    print(res.output)
    assert "Source project ID is not valid" in res.output


@pytest.mark.default_cassette("jwt-create.yaml")
@pytest.mark.vcr
@assert_authorization
def test_import_existing_project_samples__sample_project_id(mocker, credentials):
    """Test import existing project samples failure when sampe project id is used
    as source and destination.
    """
    runner = CliRunner()

    mocked_import_existing_samples = mocker.patch.object(
        APIClient,
        "import_existing_samples",
    )

    project_id = str(uuid4())
    res = runner.invoke(
        import_existing_project_samples,
        [
            project_id,
            "--source-project-id",
            project_id,
            *credentials,
        ],
    )

    assert res.exit_code == 1
    mocked_import_existing_samples.assert_not_called()
    print(res.output)
    assert "Source and destination project must be different" in res.output


@pytest.mark.default_cassette("jwt-create.yaml")
@pytest.mark.vcr
@assert_authorization
def test_import_existing_project_samples__both_sample_ids_and_source_project_id(
    mocker, credentials
):
    """Test import existing project samples failure when both sample ids and
    source project id are given.
    """
    runner = CliRunner()

    mocked_import_existing_samples = mocker.patch.object(
        APIClient,
        "import_existing_samples",
    )

    res = runner.invoke(
        import_existing_project_samples,
        [
            str(uuid4()),
            "--source-project-id",
            str(uuid4()),
            "--sample-ids",
            str(uuid4()),
            *credentials,
        ],
    )

    assert res.exit_code == 1
    mocked_import_existing_samples.assert_not_called()
    print(res.output)
    assert "Either --source-project-id or --sample-ids" in res.output


@pytest.mark.default_cassette("jwt-create.yaml")
@pytest.mark.vcr
@assert_authorization
def test_import_existing_project_samples__bad_metadata(mocker, credentials):
    """Test import existing project samples failure when optional
    metadata-json is passed, but it has a bad value.
    """
    runner = CliRunner()

    mocked_import_existing_samples = mocker.patch.object(
        APIClient,
        "import_existing_samples",
    )

    res = runner.invoke(
        import_existing_project_samples,
        [
            str(uuid4()),
            "--sample-ids",
            f"{str(uuid4())},{str(uuid4())}",
            "--metadata-json",
            '[{"foo": "bar"}',
            *credentials,
        ],
    )

    assert res.exit_code == 1
    mocked_import_existing_samples.assert_not_called()
    assert "Metadata JSON is not valid" in res.output


@pytest.mark.vcr
@assert_authorization
def test_import_existing_project_samples__server_rejects(
    mocker, credentials, project_id, recording, vcr
):
    """Test import existing project samples failure when the validation
    fails on server.
    """
    runner = CliRunner()

    if not recording:
        # Mock import_existing_samples only if using the cassettes, since we
        # mock the return value.
        project_samples_import_response = get_vcr_response(
            "/api/v2/project-samples-import/",
            vcr,
            operator.contains,
            just_body=False,
        )
        mocked_import_existing_samples = mocker.patch.object(
            APIClient,
            "import_existing_samples",
            side_effect=APIClientError(
                message=project_samples_import_response["body"]["string"],
                status_code=project_samples_import_response["status"]["code"],
            ),
        )

    res = runner.invoke(
        import_existing_project_samples,
        [
            project_id,
            "--sample-ids",
            MOCK_UUID,
            *credentials,
        ],
    )
    assert res.exit_code == 1
    if not recording:
        mocked_import_existing_samples.assert_called_once()
    assert "There was an error importing" in res.output


@pytest.mark.vcr
@assert_authorization
def test_import_existing_project_samples__success(
    mocker, credentials, project_id, sample_id_import_existing, recording, vcr
):  # pylint: disable=too-many-arguments
    """Test import existing project samples success."""
    runner = CliRunner()

    if not recording:
        # Mock import_existing_samples only if using the cassettes, since we
        # mock the return value.
        project_samples_import_response = get_vcr_response(
            "/api/v2/project-samples-import/", vcr, operator.contains
        )
        mocked_import_existing_samples = mocker.patch.object(
            APIClient,
            "import_existing_samples",
            return_value=ImportExistingSamplesModel(**project_samples_import_response),
        )

    res = runner.invoke(
        import_existing_project_samples,
        [
            project_id,
            "--sample-ids",
            sample_id_import_existing,
            *credentials,
        ],
    )
    assert res.exit_code == 0
    if not recording:
        mocked_import_existing_samples.assert_called_once()
    assert "Number of samples imported into the project" in res.output


@pytest.mark.vcr
@assert_authorization
def test_import_existing_project__from_source_project(
    mocker, credentials, project_id_import, project_id_batches, recording, vcr
):  # pylint: disable=too-many-arguments
    """Test import existing project samples success
    Using project_id_import as destination since configuration is Import FASTQs
    Using project_id_batches as source since it only contains 2 samples
    """
    runner = CliRunner()

    if not recording:
        # Mock import_existing_samples only if using the cassettes, since we
        # mock the return value.
        mocked_samples = get_vcr_response(
            "/api/v2/project-samples/", vcr, operator.contains
        )
        # Changing "mock status" to valid values
        mocked_samples["results"][0]["last_status"]["status"] = "succeeded"
        mocked_samples["results"][1]["last_status"]["status"] = "failed qc"
        mocked_get_project_samples = mocker.patch.object(
            APIClient,
            "get_project_samples",
            return_value=ProjectSamples(**mocked_samples),
        )
        project_samples_import_response = get_vcr_response(
            "/api/v2/project-samples-import/", vcr, operator.contains
        )
        mocked_import_existing_samples = mocker.patch.object(
            APIClient,
            "import_existing_samples",
            return_value=ImportExistingSamplesModel(**project_samples_import_response),
        )

    res = runner.invoke(
        import_existing_project_samples,
        [
            project_id_import,
            "--source-project-id",
            project_id_batches,
            *credentials,
        ],
    )
    assert res.exit_code == 0
    if not recording:
        mocked_get_project_samples.assert_called_once()
        mocked_import_existing_samples.assert_called_once_with(
            project_id_import, [MOCK_UUID, MOCK_UUID], None
        )
    assert "Number of samples imported into the project" in res.output


@pytest.mark.default_cassette("jwt-create.yaml")
@pytest.mark.vcr
@assert_authorization
def test_import_existing_project_samples__batch_size(
    mocker, credentials, project_id, recording, vcr  # pylint: disable=unused-argument
):  # pylint: disable=too-many-arguments
    """Test import existing project samples confirm batch size."""
    runner = CliRunner()

    sample_ids = [str(uuid4()) for _ in range(IMPORT_BATCH_SIZE * 2 + 1)]

    mocked_import_existing_samples = mocker.patch.object(
        APIClient,
        "import_existing_samples",
        return_value=ImportExistingSamplesModel(
            project_id=project_id,
            samples=[SampleImport(sample_id=sample_id) for sample_id in sample_ids],
            metadata=None,
        ),
    )

    res = runner.invoke(
        import_existing_project_samples,
        [
            project_id,
            "--sample-ids",
            ",".join(sample_ids),
            *credentials,
        ],
    )
    assert res.exit_code == 0
    assert mocked_import_existing_samples.call_count == 3
    mocked_import_existing_samples.assert_has_calls(
        [
            mock.call(project_id, samples_batch, None)
            for samples_batch in batchify(sample_ids, IMPORT_BATCH_SIZE)
        ]
    )
    assert "Number of samples imported into the project" in res.output
