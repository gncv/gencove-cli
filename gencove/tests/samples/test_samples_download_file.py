"""Test download command."""
# pylint: disable=wrong-import-order, import-error
import operator
import os
from uuid import UUID, uuid4

from click.testing import CliRunner

from gencove.client import APIClient
from gencove.command.samples.cli import download_file
from gencove.command.samples.download_file.utils import (
    download_file as util_download_file,
)
from gencove.models import SampleDetails
from gencove.tests.decorators import assert_authorization
from gencove.tests.download.vcr.filters import (
    filter_files_request,
)
from gencove.tests.filters import (
    filter_aws_headers,
    filter_jwt,
    filter_samples_request,
    filter_samples_response,
    mock_binary_response,
    replace_gencove_url_vcr,
    replace_s3_from_url,
)
from gencove.tests.samples.vcr.filters import filter_files_response_filename
from gencove.tests.utils import MOCK_CHECKSUM, MOCK_UUID, get_vcr_response

import pytest

from vcr import VCR


@pytest.fixture(scope="module")
def vcr_config():
    """VCR configuration."""
    return {
        "cassette_library_dir": "gencove/tests/samples/vcr",
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
            filter_files_request,
            replace_s3_from_url,
            filter_samples_request,
        ],
        "before_record_response": [
            filter_files_response_filename,
            filter_jwt,
            filter_aws_headers,
            mock_binary_response,
            filter_samples_response,
        ],
    }


@pytest.mark.vcr
@assert_authorization
def test_samples_download_file_local(
    credentials, mocker, recording, sample_id_download, vcr
):
    """Test command outputs to local destination."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        file_type = "fastq-r1"
        file_path = "r1.fastq.gz"
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
            file_content = get_vcr_response(f"/{file_path}", vcr)
        res = runner.invoke(
            download_file,
            [
                sample_id_download,
                file_type,
                file_path,
                *credentials,
            ],
        )
        assert res.exit_code == 0
        if not recording:
            mocked_sample_details.assert_called_once()
            with open(file_path, "rb") as local_file:
                assert file_content == local_file.read()


@pytest.mark.vcr
@assert_authorization
def test_samples_download_file_local_checksum(
    credentials, mocker, recording, sample_id_download, vcr
):
    """Test command outputs to local destination with checksum file."""
    # pylint: disable=too-many-locals
    runner = CliRunner()
    with runner.isolated_filesystem():
        file_type = "fastq-r2"
        file_path = "r2.fastq.gz"
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
            file_content = get_vcr_response(f"/{file_path}", vcr)
            get_file_checksum_response = get_vcr_response(
                "/api/v2/files/", vcr, operator.contains
            )
            mocked_get_file_checksum = mocker.patch.object(
                APIClient,
                "get_file_checksum",
                return_value=get_file_checksum_response.decode(),
            )
        res = runner.invoke(
            download_file,
            [
                sample_id_download,
                file_type,
                file_path,
                *credentials,
                "--checksum",
            ],
        )
        assert res.output == ""
        assert res.exit_code == 0
        if not recording:
            mocked_sample_details.assert_called_once()
            with open(file_path, "rb") as local_file:
                assert file_content == local_file.read()
            mocked_get_file_checksum.assert_called_once_with(
                UUID(MOCK_UUID), filename=file_path
            )
            checksum_path = f"{file_path}.sha256"
            assert os.path.exists(checksum_path)
            with open(checksum_path, "r", encoding="utf-8") as checksum_file:
                assert checksum_file.read() == f"{MOCK_CHECKSUM} *{file_path}\n"


@pytest.mark.vcr
@assert_authorization
def test_samples_download_file_local_checksum_exception(
    credentials, mocker, recording, sample_id_download, vcr
):
    """Check that checksum flag fails if file doesn't have checksum
    (r1 file).
    """
    runner = CliRunner()
    with runner.isolated_filesystem():
        file_type = "fastq-r1"
        file_path = "r1.fastq.gz"
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
                "gencove.command.samples.download_file.main.download_file",
                side_effect=util_download_file,
            )
        res = runner.invoke(
            download_file,
            [
                sample_id_download,
                file_type,
                file_path,
                *credentials,
                "--checksum",
            ],
        )
        assert res.exit_code == 1
        assert (
            "ERROR: API Client Error: Bad Request: File does not have checksum."  # noqa: E501 pylint: disable=line-too-long
            in res.stdout
        )
        if not recording:
            mocked_sample_details.assert_called_once()
            mocked_download_file.assert_called_once()
            checksum_path = f"{file_path}.sha256"
            assert not os.path.exists(checksum_path)


@pytest.mark.vcr
@assert_authorization
def test_samples_download_file_stdout(
    credentials, mocker, recording, sample_id_download, vcr
):
    """Test command outputs to stdout."""
    runner = CliRunner()
    file_type = "fastq-r1"
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
        file_content = get_vcr_response("/r1.fastq.gz", vcr)

    res = runner.invoke(
        download_file,
        [
            sample_id_download,
            file_type,
            "-",
            *credentials,
        ],
    )
    assert res.exit_code == 0
    if not recording:
        mocked_sample_details.assert_called_once()
        assert file_content == res.output.encode()


@pytest.mark.vcr
def test_samples_download_file_directory(mocker):
    """Test command fails when writing to directory."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        mocked_login = mocker.patch.object(APIClient, "login")
        res = runner.invoke(
            download_file,
            [
                str(uuid4()),
                "file_type",
                ".",
                "--email",
                "foo@bar.com",
                "--password",
                "12345",
            ],
        )
        assert res.exit_code == 1
        mocked_login.assert_not_called()
        assert (
            "ERROR: Please specify a file path (not directory path) for DESTINATION"  # noqa: E501 line too long pylint: disable=line-too-long
            in res.output
        )
