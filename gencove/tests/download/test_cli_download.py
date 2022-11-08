"""Test download command."""
# pylint: disable=wrong-import-order, import-error, too-many-lines
import io
import json
import operator
import os
import sys
from unittest.mock import call
from uuid import UUID, uuid4

from click import echo
from click.testing import CliRunner

from gencove.cli import download
from gencove.client import APIClient
from gencove.command.download.utils import download_file
from gencove.models import (
    ProjectSamples,
    SampleDetails,
    SampleMetadata,
    SampleQC,
)
from gencove.tests.decorators import assert_authorization
from gencove.tests.download.vcr.filters import (
    filter_files_request,
    filter_files_response,
    filter_project_samples_request,
    filter_sample_metadata_request,
    filter_sample_quality_controls_request,
)
from gencove.tests.filters import (
    filter_aws_headers,
    filter_file_types_request,
    filter_jwt,
    filter_project_samples_response,
    filter_samples_request,
    filter_samples_response,
    mock_binary_response,
    replace_gencove_url_vcr,
    replace_s3_from_url,
)
from gencove.tests.utils import MOCK_CHECKSUM, MOCK_UUID, get_vcr_response

from pydantic.networks import HttpUrl

import pytest

from vcr import VCR


@pytest.fixture(scope="module")
def vcr_config():
    """VCR configuration."""
    return {
        "cassette_library_dir": "gencove/tests/download/vcr",
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
            filter_file_types_request,
            filter_files_request,
            filter_project_samples_request,
            filter_samples_request,
            filter_sample_quality_controls_request,
            filter_sample_metadata_request,
            replace_s3_from_url,
        ],
        "before_record_response": [
            filter_files_response,
            filter_jwt,
            filter_project_samples_response,
            filter_samples_response,
            mock_binary_response,
            filter_aws_headers,
        ],
    }


@pytest.mark.vcr
@assert_authorization
def test_no_required_options(credentials, mocker):  # pylint: disable=unused-argument
    """Test that command exits without project id or sample id provided."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        os.mkdir("cli_test_data")
        res = runner.invoke(
            download,
            [
                "cli_test_data",
                "--project-id",
                "11111111-1111-1111-1111-111111111111",
                *credentials,
            ],
        )
        assert res.exit_code == 1


@pytest.mark.vcr
def test_both_project_id_and_sample_ids_provided(credentials, mocker):
    """Command exits if both project id and sample ids are provided."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        os.mkdir("cli_test_data")
        mocked_login = mocker.patch.object(APIClient, "login")
        res = runner.invoke(
            download,
            [
                "cli_test_data",
                "--project-id",
                "11111111-1111-1111-1111-111111111111",
                "--sample-ids",
                "1,2,3",
                *credentials,
            ],
        )
    assert res.exit_code == 1
    mocked_login.assert_not_called()


@pytest.mark.vcr
@assert_authorization
def test_project_id_provided(credentials, mocker, project_id_download, recording, vcr):
    """Check happy flow."""
    # pylint: disable=too-many-locals
    runner = CliRunner()
    with runner.isolated_filesystem():
        if not recording:
            # Mock only if using the cassettes, since we mock the return value.
            get_project_samples_response = get_vcr_response(
                "/api/v2/project-samples/", vcr, operator.contains
            )
            mocked_project_samples = mocker.patch.object(
                APIClient,
                "get_project_samples",
                return_value=ProjectSamples(**get_project_samples_response),
            )
            get_sample_details_response = get_vcr_response(
                "/api/v2/samples/", vcr, operator.contains
            )
            mocked_sample_details = mocker.patch.object(
                APIClient,
                "get_sample_details",
                return_value=SampleDetails(**get_sample_details_response),
            )
            get_sample_qc_metrics_response = get_vcr_response(
                "/api/v2/sample-quality-controls/", vcr, operator.contains
            )
            mocked_qc_metrics = mocker.patch.object(
                APIClient,
                "get_sample_qc_metrics",
                return_value=SampleQC(**get_sample_qc_metrics_response),
            )
            get_metadata_response = get_vcr_response(
                "/api/v2/sample-metadata/", vcr, operator.contains
            )
            mocked_get_metadata = mocker.patch.object(
                APIClient,
                "get_metadata",
                return_value=SampleMetadata(**get_metadata_response),
            )
        mocked_download_file = mocker.patch(
            "gencove.command.download.main.download_file",
            side_effect=download_file,
        )
        res = runner.invoke(
            download,
            [
                "cli_test_data",
                "--project-id",
                project_id_download,
                *credentials,
            ],
        )
        assert res.exit_code == 0
        if not recording:
            mocked_project_samples.assert_called_once()
            mocked_sample_details.assert_called_once()
            mocked_qc_metrics.assert_called_once()
            mocked_get_metadata.assert_called_once()
        assert mocked_download_file.call_count == 2


@pytest.mark.vcr
@assert_authorization
def test_sample_ids_provided(credentials, mocker, recording, sample_id_download, vcr):
    """Check happy flow with sample ids."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        if not recording:
            # Mock only if using the cassettes, since we mock the return value.
            get_sample_details_response = get_vcr_response(
                "/api/v2/samples/", vcr, operator.contains
            )
            mocked_sample_details = mocker.patch.object(
                APIClient,
                "get_sample_details",
                return_value=SampleDetails(**get_sample_details_response),
            )
            get_sample_qc_metrics_response = get_vcr_response(
                "/api/v2/sample-quality-controls/", vcr, operator.contains
            )
            mocked_qc_metrics = mocker.patch.object(
                APIClient,
                "get_sample_qc_metrics",
                return_value=SampleQC(**get_sample_qc_metrics_response),
            )
            get_metadata_response = get_vcr_response(
                "/api/v2/sample-metadata/", vcr, operator.contains
            )
            mocked_get_metadata = mocker.patch.object(
                APIClient,
                "get_metadata",
                return_value=SampleMetadata(**get_metadata_response),
            )
            mocked_download_file = mocker.patch(
                "gencove.command.download.main.download_file",
                side_effect=download_file,
            )
        res = runner.invoke(
            download,
            [
                "cli_test_data",
                "--sample-ids",
                sample_id_download,
                *credentials,
            ],
        )
        assert res.exit_code == 0
        if not recording:
            mocked_sample_details.assert_called_once()
            mocked_qc_metrics.assert_called_once()
            mocked_get_metadata.assert_called_once()
            calls = [
                call(
                    f"cli_test_data/mock_client_id/{MOCK_UUID}/r1.fastq.gz",
                    HttpUrl(
                        url="https://example.com/r1.fastq.gz",
                        scheme="https",
                        host="example.com",
                    ),
                    True,
                    False,
                ),
                call(
                    f"cli_test_data/mock_client_id/{MOCK_UUID}/r2.fastq.gz",
                    HttpUrl(
                        url="https://example.com/r2.fastq.gz",
                        scheme="https",
                        host="example.com",
                    ),
                    True,
                    False,
                ),
            ]
            mocked_download_file.assert_has_calls(calls)


@pytest.mark.vcr
@assert_authorization
def test_sample_ids_provided_no_qc_file(
    credentials, mocker, recording, sample_id_download, vcr
):
    """Check flow with sample ids and no file present."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        mocked_sample_details = mocker.patch.object(
            APIClient,
            "get_sample_details",
            return_value=SampleDetails(
                **{
                    "id": sample_id_download,
                    "client_id": "1",
                    "last_status": {
                        "id": str(uuid4()),
                        "status": "succeeded",
                        "created": "2020-07-28T12:46:22.719862Z",
                    },
                    "archive_last_status": {
                        "id": str(uuid4()),
                        "status": "available",
                        "created": "2020-07-28T12:46:22.719862Z",
                        "transition_cutoff": "2020-08-28T12:46:22.719862Z",
                    },
                    "files": [],
                }
            ),
        )
        if not recording:
            # Mock only if using the cassettes, since we mock the return value.
            get_sample_qc_metrics_response = get_vcr_response(
                "/api/v2/sample-quality-controls/", vcr, operator.contains
            )
            mocked_qc_metrics = mocker.patch.object(
                APIClient,
                "get_sample_qc_metrics",
                return_value=SampleQC(**get_sample_qc_metrics_response),
            )
            get_metadata_response = get_vcr_response(
                "/api/v2/sample-metadata/", vcr, operator.contains
            )
            mocked_get_metadata = mocker.patch.object(
                APIClient,
                "get_metadata",
                return_value=SampleMetadata(**get_metadata_response),
            )
        mocked_download_file = mocker.patch(
            "gencove.command.download.main.download_file",
            side_effect=download_file,
        )
        res = runner.invoke(
            download,
            [
                "cli_test_data",
                "--sample-ids",
                sample_id_download,
                *credentials,
            ],
        )
        assert res.exit_code == 0
        mocked_download_file.assert_not_called()
        if not recording:
            mocked_sample_details.assert_called_once()
            mocked_qc_metrics.assert_called_once()
            mocked_get_metadata.assert_called_once()


@pytest.mark.vcr
@assert_authorization
def test_create_checksum_file(credentials, mocker, recording, sample_id_download, vcr):
    """Check checksums flag."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        if not recording:
            # Mock only if using the cassettes, since we mock the return value.
            get_sample_details_response = get_vcr_response(
                "/api/v2/samples/", vcr, operator.contains
            )
            mocked_sample_details = mocker.patch.object(
                APIClient,
                "get_sample_details",
                return_value=SampleDetails(**get_sample_details_response),
            )
            mocked_download_file = mocker.patch(
                "gencove.command.download.main.download_file",
                side_effect=download_file,
            )
            get_file_checksum_response = get_vcr_response(
                "/api/v2/files/", vcr, operator.contains
            )
            mocked_get_file_checksum = mocker.patch.object(
                APIClient,
                "get_file_checksum",
                return_value=get_file_checksum_response.decode(),
            )
        res = runner.invoke(
            download,
            [
                "cli_test_data",
                "--sample-ids",
                sample_id_download,
                *credentials,
                "--file-types",
                "fastq-r2",
                "--checksums",
            ],
        )
        assert res.exit_code == 0
        if not recording:
            mocked_sample_details.assert_called_once()
            mocked_download_file.assert_called_once_with(
                f"cli_test_data/mock_client_id/{MOCK_UUID}/r2.fastq.gz",
                HttpUrl(
                    url="https://example.com/r2.fastq.gz",
                    scheme="https",
                    host="example.com",
                ),
                True,
                False,
            )
            mocked_get_file_checksum.assert_called_once_with(UUID(MOCK_UUID))
            checksum_path = (
                f"cli_test_data/mock_client_id/{MOCK_UUID}/r2.fastq.gz.sha256"
            )
            assert os.path.exists(checksum_path)
            with open(checksum_path, "r", encoding="utf-8") as checksum_file:
                assert (
                    checksum_file.read()
                    == f"{MOCK_CHECKSUM} *{MOCK_UUID}_R2.fastq.gz\n"
                )


@pytest.mark.vcr
@assert_authorization
def test_create_checksum_file_exception(
    credentials, mocker, recording, sample_id_download, vcr
):
    """Check that checksums flag fails if file doesn't have checksum
    (r1 file).
    """
    runner = CliRunner()
    with runner.isolated_filesystem():
        if not recording:
            # Mock only if using the cassettes, since we mock the return value.
            get_sample_details_response = get_vcr_response(
                "/api/v2/samples/", vcr, operator.contains
            )
            mocked_sample_details = mocker.patch.object(
                APIClient,
                "get_sample_details",
                return_value=SampleDetails(**get_sample_details_response),
            )
            mocked_download_file = mocker.patch(
                "gencove.command.download.main.download_file",
                side_effect=download_file,
            )
        res = runner.invoke(
            download,
            [
                "cli_test_data",
                "--sample-ids",
                sample_id_download,
                *credentials,
                "--file-types",
                "fastq-r1",
                "--checksums",
            ],
        )
        assert res.exit_code == 1
        assert (
            "ERROR: API Client Error: Bad Request: File does not have checksum."  # noqa: E501 pylint: disable=line-too-long
            in res.stdout
        )
        if not recording:
            mocked_sample_details.assert_called_once()
            mocked_download_file.assert_called_once_with(
                f"cli_test_data/mock_client_id/{MOCK_UUID}/r1.fastq.gz",
                HttpUrl(
                    url="https://example.com/r1.fastq.gz",
                    scheme="https",
                    host="example.com",
                ),
                True,
                False,
            )
            file_path = f"cli_test_data/mock_client_id/{MOCK_UUID}/r1.fastq.gz"
            checksum_path = f"{file_path}.sha256"
            assert not os.path.exists(checksum_path)


def test_multiple_credentials_not_allowed(mocker):
    """Test that in providing multiple credentials is not allowed."""
    runner = CliRunner()
    mocked_login = mocker.patch.object(APIClient, "login")
    res = runner.invoke(
        download,
        [
            "some_test_data",
            "--sample-ids",
            "0",
            "--email",
            "foo@bar.com",
            "--password",
            "123",
            "--api-key",
            "foobar",
        ],
    )
    assert res.exit_code == 1
    assert "Please provide either username/password or API key." in res.output
    mocked_login.assert_not_called()


@pytest.mark.vcr
@assert_authorization
def test_download_stdout_no_flag(
    credentials, mocker, project_id_download, recording, vcr
):
    """Test command exits if no flag provided and stdout defined."""
    runner = CliRunner()
    if not recording:
        # Mock only if using the cassettes, since we mock the return value.
        get_project_samples_response = get_vcr_response(
            "/api/v2/project-samples/", vcr, operator.contains
        )
        mocked_project_samples = mocker.patch.object(
            APIClient,
            "get_project_samples",
            return_value=ProjectSamples(**get_project_samples_response),
        )
    res = runner.invoke(
        download,
        [
            "-",
            "--project-id",
            project_id_download,
            *credentials,
        ],
    )
    assert res.exit_code == 1
    output_line = io.BytesIO()
    sys.stdout = output_line
    echo("ERROR: Cannot have - as a destination without download-urls.")
    assert output_line.getvalue() in res.output.encode()
    if not recording:
        mocked_project_samples.assert_called_once()


@pytest.mark.vcr
@assert_authorization
def test_download_stdout_with_flag(
    credentials, mocker, project_id_download, recording, vcr
):
    """Test command outputs json to stdout."""
    # pylint: disable=too-many-locals
    runner = CliRunner()
    if not recording:
        # Mock only if using the cassettes, since we mock the return value.
        get_project_samples_response = get_vcr_response(
            "/api/v2/project-samples/", vcr, operator.contains
        )
        mocked_project_samples = mocker.patch.object(
            APIClient,
            "get_project_samples",
            return_value=ProjectSamples(**get_project_samples_response),
        )
        get_sample_details_response = get_vcr_response(
            "/api/v2/samples/", vcr, operator.contains
        )
        sample = SampleDetails(**get_sample_details_response)
        mocked_sample_details = mocker.patch.object(
            APIClient,
            "get_sample_details",
            return_value=sample,
        )
    res = runner.invoke(
        download,
        [
            "-",
            "--project-id",
            project_id_download,
            *credentials,
            "--download-urls",
        ],
    )
    assert res.exit_code == 0
    if not recording:
        mocked_project_samples.assert_called_once()
        mocked_sample_details.assert_called_once()
        output_line = io.BytesIO()
        sys.stdout = output_line
        for _ in get_project_samples_response["results"]:
            archive_last_status_created = sample.archive_last_status.created.isoformat()
            download_url_1 = "https://example.com/r1.fastq.gz"
            download_url_2 = "https://example.com/r2.fastq.gz"
            mocked_result = json.dumps(
                [
                    {
                        "gencove_id": MOCK_UUID,
                        "client_id": "mock_client_id",
                        "last_status": {
                            "id": MOCK_UUID,
                            "status": sample.last_status.status,
                            "created": sample.last_status.created.isoformat(),
                        },
                        "archive_last_status": {
                            "id": MOCK_UUID,
                            "status": sample.archive_last_status.status,
                            "created": archive_last_status_created,
                            "transition_cutoff": None,
                        },
                        "files": {
                            "fastq-r1": {
                                "id": MOCK_UUID,
                                "download_url": download_url_1,
                                "checksum_sha256": "",
                            },
                            "fastq-r2": {
                                "id": MOCK_UUID,
                                "download_url": download_url_2,
                                "checksum_sha256": MOCK_CHECKSUM,
                            },
                        },
                    }
                ],
                indent=4,
            )
            echo(mocked_result)
        assert output_line.getvalue() in res.output.encode()


@pytest.mark.vcr
@assert_authorization
def test_download_urls_to_file(
    credentials, mocker, project_id_download, recording, vcr
):
    """Test saving downloaded urls output to a json file."""
    # pylint: disable=too-many-locals
    runner = CliRunner()
    if not recording:
        # Mock only if using the cassettes, since we mock the return value.
        get_project_samples_response = get_vcr_response(
            "/api/v2/project-samples/", vcr, operator.contains
        )
        mocked_project_samples = mocker.patch.object(
            APIClient,
            "get_project_samples",
            return_value=ProjectSamples(**get_project_samples_response),
        )
        get_sample_details_response = get_vcr_response(
            "/api/v2/samples/", vcr, operator.contains
        )
        sample = SampleDetails(**get_sample_details_response)
        mocked_sample_details = mocker.patch.object(
            APIClient,
            "get_sample_details",
            return_value=sample,
        )
    with runner.isolated_filesystem():
        res = runner.invoke(
            download,
            [
                "output.json",
                "--project-id",
                project_id_download,
                *credentials,
                "--download-urls",
            ],
        )
        assert res.exit_code == 0
        output_file = []
        if not recording:
            for _ in get_project_samples_response["results"]:
                archive_last_status_created = (
                    sample.archive_last_status.created.isoformat()
                )
                download_url_1 = "https://example.com/r1.fastq.gz"
                download_url_2 = "https://example.com/r2.fastq.gz"
                output_file.append(
                    {
                        "gencove_id": MOCK_UUID,
                        "client_id": "mock_client_id",
                        "last_status": {
                            "id": MOCK_UUID,
                            "status": sample.last_status.status,
                            "created": sample.last_status.created.isoformat(),
                        },
                        "archive_last_status": {
                            "id": MOCK_UUID,
                            "status": sample.archive_last_status.status,
                            "created": archive_last_status_created,
                            "transition_cutoff": None,
                        },
                        "files": {
                            "fastq-r1": {
                                "id": MOCK_UUID,
                                "download_url": download_url_1,
                                "checksum_sha256": "",
                            },
                            "fastq-r2": {
                                "id": MOCK_UUID,
                                "download_url": download_url_2,
                                "checksum_sha256": MOCK_CHECKSUM,
                            },
                        },
                    }
                )
            with open("output.json", "r", encoding="utf-8") as json_file:
                assert output_file == json.load(json_file)
            mocked_project_samples.assert_called_once()
            mocked_sample_details.assert_called_once()


@pytest.mark.vcr
@assert_authorization
def test_download_no_progress(credentials, mocker, recording, sample_id_download, vcr):
    """Test command doesn't show progress bar."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        if not recording:
            # Mock only if using the cassettes, since we mock the return value.
            get_sample_details_response = get_vcr_response(
                "/api/v2/samples/", vcr, operator.contains
            )
            mocked_sample_details = mocker.patch.object(
                APIClient,
                "get_sample_details",
                return_value=SampleDetails(**get_sample_details_response),
            )
            get_sample_qc_metrics_response = get_vcr_response(
                "/api/v2/sample-quality-controls/", vcr, operator.contains
            )
            mocked_qc_metrics = mocker.patch.object(
                APIClient,
                "get_sample_qc_metrics",
                return_value=SampleQC(**get_sample_qc_metrics_response),
            )
            get_metadata_response = get_vcr_response(
                "/api/v2/sample-metadata/", vcr, operator.contains
            )
            mocked_get_metadata = mocker.patch.object(
                APIClient,
                "get_metadata",
                return_value=SampleMetadata(**get_metadata_response),
            )
        mocked_download_file = mocker.patch(
            "gencove.command.download.main.download_file",
            side_effect=download_file,
        )
        res = runner.invoke(
            download,
            [
                "cli_test_data",
                "--sample-ids",
                sample_id_download,
                *credentials,
                "--no-progress",
            ],
        )
        assert res.exit_code == 0
        if not recording:
            mocked_download_file.assert_has_calls(
                [
                    call(
                        f"cli_test_data/mock_client_id/{MOCK_UUID}/r1.fastq.gz",  # noqa: E501 pylint: disable=line-too-long
                        HttpUrl(
                            url="https://example.com/r1.fastq.gz",
                            scheme="https",
                            host="example.com",
                        ),
                        True,
                        True,
                    ),
                    call(
                        f"cli_test_data/mock_client_id/{MOCK_UUID}/r2.fastq.gz",  # noqa: E501 pylint: disable=line-too-long
                        HttpUrl(
                            url="https://example.com/r2.fastq.gz",
                            scheme="https",
                            host="example.com",
                        ),
                        True,
                        True,
                    ),
                ]
            )
            mocked_sample_details.assert_called_once()
            mocked_qc_metrics.assert_called_once()
            mocked_get_metadata.assert_called_once()


@pytest.mark.vcr
@assert_authorization
def test_project_id_provided_skip_existing_qc_and_metadata(
    credentials, mocker, project_id_download, recording, vcr
):
    """Check happy flow."""
    # pylint: disable=too-many-locals
    runner = CliRunner()
    with runner.isolated_filesystem():
        if not recording:
            # Mock only if using the cassettes, since we mock the return value.
            get_project_samples_response = get_vcr_response(
                "/api/v2/project-samples/", vcr, operator.contains
            )
            mocked_project_samples = mocker.patch.object(
                APIClient,
                "get_project_samples",
                return_value=ProjectSamples(**get_project_samples_response),
            )
            get_sample_details_response = get_vcr_response(
                "/api/v2/samples/", vcr, operator.contains
            )
            mocked_sample_details = mocker.patch.object(
                APIClient,
                "get_sample_details",
                return_value=SampleDetails(**get_sample_details_response),
            )
            get_sample_qc_metrics_response = get_vcr_response(
                "/api/v2/sample-quality-controls/", vcr, operator.contains
            )
            mocked_qc_metrics = mocker.patch.object(
                APIClient,
                "get_sample_qc_metrics",
                return_value=SampleQC(**get_sample_qc_metrics_response),
            )
            get_metadata_response = get_vcr_response(
                "/api/v2/sample-metadata/", vcr, operator.contains
            )
            mocked_get_metadata = mocker.patch.object(
                APIClient,
                "get_metadata",
                return_value=SampleMetadata(**get_metadata_response),
            )
        mocked_download_file = mocker.patch(
            "gencove.command.download.main.download_file",
            side_effect=download_file,
        )
        res = runner.invoke(
            download,
            [
                "cli_test_data",
                "--project-id",
                project_id_download,
                *credentials,
                "--no-skip-existing",
            ],
        )
        assert res.exit_code == 0
        if not recording:
            mocked_project_samples.assert_called_once()
            mocked_sample_details.assert_called_once()
            mocked_qc_metrics.assert_called_once()
            mocked_get_metadata.assert_called_once()
        assert mocked_download_file.call_count == 2

        # call it the second time
        mocked_qc_metrics = mocker.patch.object(APIClient, "get_sample_qc_metrics")
        mocked_get_metadata = mocker.patch.object(APIClient, "get_metadata")
        res = runner.invoke(
            download,
            [
                "cli_test_data",
                "--project-id",
                project_id_download,
                *credentials,
                "--skip-existing",
            ],
        )
        assert res.exit_code == 0
        mocked_qc_metrics.assert_not_called()
        mocked_get_metadata.assert_not_called()


@pytest.mark.vcr
@assert_authorization
def test_download_not_working_because_archived(
    archived_sample, credentials, mocker, recording, vcr
):
    """Test command doesn't download archived files."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        if not recording:
            # Mock only if using the cassettes, since we mock the return value.
            get_sample_details_response = get_vcr_response(
                "/api/v2/samples/", vcr, operator.contains
            )
            mocked_sample_details = mocker.patch.object(
                APIClient,
                "get_sample_details",
                return_value=SampleDetails(**get_sample_details_response),
            )
        mocked_qc_metrics = mocker.patch.object(APIClient, "get_sample_qc_metrics")
        mocked_get_metadata = mocker.patch.object(APIClient, "get_metadata")
        mocked_download_file = mocker.patch(
            "gencove.command.download.main.download_file",
        )
        res = runner.invoke(
            download,
            [
                "cli_test_data",
                "--sample-ids",
                archived_sample,
                *credentials,
            ],
        )
        assert res.exit_code == 1
        assert "is archived and cannot be downloaded " in res.output
        if not recording:
            mocked_sample_details.assert_called_once()
        mocked_qc_metrics.assert_not_called()
        mocked_get_metadata.assert_not_called()
        mocked_download_file.assert_not_called()


@pytest.mark.default_cassette("jwt-create.yaml")
@pytest.mark.vcr
@assert_authorization
def test_project_id_provided_filter_not_archived(credentials, mocker):
    """Check happy flow."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        mocked_project_samples = mocker.patch.object(
            APIClient,
            "get_project_samples",
            return_value=ProjectSamples(**{"results": [], "meta": {"next": None}}),
        )
        mocked_sample_details = mocker.patch.object(APIClient, "get_sample_details")
        mocked_qc_metrics = mocker.patch.object(APIClient, "get_sample_qc_metrics")
        mocked_get_metadata = mocker.patch.object(APIClient, "get_metadata")
        mocked_download_file = mocker.patch(
            "gencove.command.download.main.download_file"
        )
        res = runner.invoke(
            download,
            [
                "cli_test_data",
                "--project-id",
                "123",
                *credentials,
            ],
        )
        assert res.exit_code == 1
        mocked_project_samples.assert_called_once()
        mocked_qc_metrics.assert_not_called()
        mocked_get_metadata.assert_not_called()
        mocked_download_file.assert_not_called()
        mocked_sample_details.assert_not_called()


@pytest.mark.vcr
def test_invalid_file_types_project_id_provided(
    credentials, mocker, project_id_download, recording, vcr
):
    """Fails when an invalid file type is provided for a project"""
    # pylint: disable=too-many-locals
    runner = CliRunner()
    with runner.isolated_filesystem():
        if not recording:
            # Mock only if using the cassettes, since we mock the return value.
            get_project_samples_response = get_vcr_response(
                "/api/v2/project-samples/", vcr, operator.contains
            )
            mocked_project_samples = mocker.patch.object(
                APIClient,
                "get_project_samples",
                return_value=ProjectSamples(**get_project_samples_response),
            )
        mocked_sample_details = mocker.patch.object(APIClient, "get_sample_details")
        mocked_qc_metrics = mocker.patch.object(APIClient, "get_sample_qc_metrics")
        mocked_get_metadata = mocker.patch.object(APIClient, "get_metadata")
        mocked_download_file = mocker.patch(
            "gencove.command.download.main.download_file",
            side_effect=download_file,
        )
        res = runner.invoke(
            download,
            [
                "cli_test_data",
                "--project-id",
                project_id_download,
                *credentials,
                "--file-types",
                "call_capture-forced_vcf",
            ],
        )
        assert res.exit_code == 1
        assert "ERROR: Invalid file types: call_capture-forced_vcf." in res.stdout
        if not recording:
            mocked_project_samples.assert_called_once()
        mocked_sample_details.assert_not_called()
        mocked_qc_metrics.assert_not_called()
        mocked_get_metadata.assert_not_called()
        mocked_download_file.assert_not_called()


@pytest.mark.vcr
def test_invalid_file_types_sample_ids_provided(
    credentials, mocker, sample_id_download, recording, vcr
):
    """Fails when an invalid file type is provided for a sample"""
    # pylint: disable=too-many-locals
    runner = CliRunner()
    with runner.isolated_filesystem():
        if not recording:
            # Mock only if using the cassettes, since we mock the return value.
            get_sample_details_response = get_vcr_response(
                "/api/v2/samples/", vcr, operator.contains
            )
            mocked_sample_details = mocker.patch.object(
                APIClient,
                "get_sample_details",
                return_value=SampleDetails(**get_sample_details_response),
            )
        mocked_qc_metrics = mocker.patch.object(APIClient, "get_sample_qc_metrics")
        mocked_get_metadata = mocker.patch.object(APIClient, "get_metadata")
        mocked_download_file = mocker.patch(
            "gencove.command.download.main.download_file",
            side_effect=download_file,
        )
        res = runner.invoke(
            download,
            [
                "cli_test_data",
                "--sample-ids",
                sample_id_download,
                *credentials,
                "--file-types",
                "fastqr1",
            ],
        )
        assert res.exit_code == 1
        assert "ERROR: Invalid file types: fastqr1." in res.stdout
        mocked_sample_details.assert_not_called()
        mocked_qc_metrics.assert_not_called()
        mocked_get_metadata.assert_not_called()
        mocked_download_file.assert_not_called()
