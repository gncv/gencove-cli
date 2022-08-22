"""Test project's batches list command."""
# pylint: disable=wrong-import-order, import-error
import operator
from uuid import uuid4

from click.testing import CliRunner

from gencove.client import APIClient, APIClientTimeout  # noqa: I100
from gencove.command.download.utils import download_file
from gencove.command.projects.cli import get_batch
from gencove.models import BatchDetail
from gencove.tests.decorators import assert_authorization
from gencove.tests.filters import (
    filter_aws_headers,
    filter_jwt,
    mock_binary_response,
    replace_gencove_url_vcr,
    replace_s3_from_url,
)
from gencove.tests.projects.vcr.filters import (
    filter_batches_request,
    filter_batches_response,
)
from gencove.tests.upload.vcr.filters import filter_volatile_dates
from gencove.tests.utils import get_vcr_response

from pydantic.networks import HttpUrl

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
            filter_batches_request,
            replace_s3_from_url,
        ],
        "before_record_response": [
            filter_jwt,
            filter_volatile_dates,
            filter_batches_response,
            mock_binary_response,
            filter_aws_headers,
        ],
    }


@pytest.mark.default_cassette("jwt-create.yaml")
@pytest.mark.vcr
@assert_authorization
def test_get_batch__empty(credentials, mocker):
    """Test project has not batches."""
    runner = CliRunner()
    batch_id = str(uuid4())
    mocked_get_batch = mocker.patch.object(
        APIClient,
        "get_batch",
        return_value=BatchDetail(
            id=batch_id,
            name="cli-test-1",
            batch_type="batch-type-1",
            sample_ids=[str(uuid4()), str(uuid4())],
            last_status=dict(
                id=str(uuid4()),
                status="running",
                created="2020-08-02T22:13:54.547167Z",
            ),
            files=[],
        ),
    )

    res = runner.invoke(get_batch, [batch_id, *credentials])
    assert res.exit_code == 1
    mocked_get_batch.assert_called_once()
    assert res.output == (
        "ERROR: There are no deliverables available for batch"
        f" {batch_id}.\nAborted!\n"
    )


@pytest.mark.vcr
@assert_authorization
def test_get_batch__not_empty(batch_id, credentials, mocker, recording, vcr):
    """Test project batches being outputed to the shell."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        if not recording:
            # Mock get_batch only if using the cassettes, since we mock the
            # return value.
            get_batch_response = get_vcr_response(
                "/api/v2/batches/", vcr, operator.contains
            )
            mocked_get_batch = mocker.patch.object(
                APIClient,
                "get_batch",
                return_value=BatchDetail(**get_batch_response),
            )
            mocked_download_file = mocker.patch(
                "gencove.command.projects.get_batch.main.download.utils."
                "download_file",
                side_effect=download_file,
            )
        res = runner.invoke(
            get_batch,
            [
                batch_id,
                *credentials,
                "--output-filename",
                "test.zip",
            ],
        )
    assert res.exit_code == 0

    if not recording:
        mocked_get_batch.assert_called_once()
        mocked_download_file.assert_called_once_with(
            "test.zip",
            HttpUrl(
                url="https://example.com/report.zip",
                scheme="https",
                host="example.com",
            ),
            no_progress=False,
        )


@pytest.mark.vcr
@assert_authorization
def test_get_batch__no_progress_not_empty(
    batch_id, credentials, mocker, recording, vcr
):
    """Test project batches being outputed to the shell without progress."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        if not recording:
            # Mock get_batch only if using the cassettes, since we mock the
            # return value.
            get_batch_response = get_vcr_response(
                "/api/v2/batches/", vcr, operator.contains
            )
            mocked_get_batch = mocker.patch.object(
                APIClient,
                "get_batch",
                return_value=BatchDetail(**get_batch_response),
            )
            mocked_download_file = mocker.patch(
                "gencove.command.projects.get_batch.main.download.utils."
                "download_file",
                side_effect=download_file,
            )
        res = runner.invoke(
            get_batch,
            [
                batch_id,
                *credentials,
                "--output-filename",
                "test.zip",
                "--no-progress",
            ],
        )
    assert res.exit_code == 0
    if not recording:
        mocked_get_batch.assert_called_once()
        mocked_download_file.assert_called_once_with(
            "test.zip",
            HttpUrl(
                url="https://example.com/report.zip",
                scheme="https",
                host="example.com",
            ),
            no_progress=True,
        )


@pytest.mark.default_cassette("jwt-create.yaml")
@pytest.mark.vcr
@assert_authorization
def test_get_batch__not_empty__slow_response_retry(credentials, mocker):
    """Test project batches slow response retry."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        batch_id = str(uuid4())
        mocked_get_batch = mocker.patch.object(
            APIClient,
            "get_batch",
            side_effect=APIClientTimeout("Could not connect to the api server"),
        )
        mocked_download_file = mocker.patch(
            "gencove.command.projects.get_batch.main.download.utils.download_file"
        )
        res = runner.invoke(
            get_batch,
            [
                batch_id,
                *credentials,
                "--output-filename",
                "test.zip",
            ],
        )
    assert res.exit_code == 1
    assert mocked_get_batch.call_count == 2
    mocked_download_file.assert_not_called()
