"""Tests upload command of Gencove CLI."""

# pylint: disable=too-many-lines, import-error

import json
import operator
import os
from uuid import uuid4

from click.testing import CliRunner


from gencove.cli import upload
from gencove.client import APIClient, APIClientError, APIClientTimeout
from gencove.command.upload.utils import upload_file
from gencove.constants import ApiEndpoints, UPLOAD_PREFIX
from gencove.models import SampleSheet, UploadSamples, UploadsPostData
from gencove.tests.decorators import assert_authorization
from gencove.tests.filters import (
    filter_aws_headers,
    filter_jwt,
    replace_gencove_url_vcr,
)
from gencove.tests.upload.vcr.filters import (
    filter_project_samples_request,
    filter_project_samples_response,
    filter_sample_sheet_response,
    filter_upload_credentials_response,
    filter_upload_post_data_response,
    filter_upload_request,
    filter_volatile_dates,
)
from gencove.tests.utils import get_vcr_response
from gencove.utils import get_regular_progress_bar, get_s3_client_refreshable

import pytest  # pylint: disable=wrong-import-order

from vcr import VCR  # pylint: disable=wrong-import-order


@pytest.fixture(scope="module")
def vcr_config():
    """VCR configuration."""
    return {
        "cassette_library_dir": "gencove/tests/upload/vcr",
        "filter_headers": [
            "Authorization",
            "Content-Length",
            "User-Agent",
            "X-Amz-Security-Token",
            "X-Amz-Date",
        ],
        "filter_post_data_parameters": [
            ("email", "email@example.com"),
            ("password", "mock_password"),
        ],
        "filter_query_parameters": [("search", "gncv://cli-mock/test.fastq.gz")],
        "match_on": ["method", "scheme", "port", "path", "query"],
        "path_transformer": VCR.ensure_suffix(".yaml"),
        "before_record_request": [
            replace_gencove_url_vcr,
            filter_upload_request,
            filter_project_samples_request,
        ],
        "before_record_response": [
            filter_jwt,
            filter_upload_credentials_response,
            filter_upload_post_data_response,
            filter_volatile_dates,
            filter_aws_headers,
            filter_sample_sheet_response,
            filter_project_samples_response,
        ],
    }


@pytest.mark.vcr
@assert_authorization
def test_upload(credentials, vcr, recording, mocker):
    """Sanity check that upload is ok."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        os.mkdir("cli_test_data")
        with open("cli_test_data/test.fastq.gz", "w", encoding="utf-8") as fastq_file:
            fastq_file.write("AAABBB")
        mocked_get_credentials = mocker.patch(
            "gencove.command.upload.main.get_s3_client_refreshable",
            side_effect=get_s3_client_refreshable,
        )
        if not recording:
            # Mock get_upload credentials only if using the cassettes, since
            # we mock the return value.
            response = get_vcr_response("/api/v2/uploads-post-data/", vcr)
            mocked_get_upload_details = mocker.patch.object(
                APIClient,
                "get_upload_details",
                return_value=UploadsPostData(**response),
            )
        mocked_upload_file = mocker.patch(
            "gencove.command.upload.main.upload_file", side_effect=upload_file
        )

        res = runner.invoke(
            upload,
            ["cli_test_data", *credentials],
        )
        assert not res.exception
        assert res.exit_code == 0
        assert "Uploading cli_test_data/test.fastq.gz to gncv://" in res.output
        assert "All files were successfully uploaded." in res.output
        mocked_get_credentials.assert_called_once()
        if not recording:
            mocked_get_upload_details.assert_called_once()
        mocked_upload_file.assert_called_once()
        assert not mocked_upload_file.call_args[1]["no_progress"]


@pytest.mark.vcr
@assert_authorization
def test_upload_no_files_found(
    credentials, mocker, recording, using_api_key, vcr
):  # pylint: disable=unused-argument
    """Test that no fastq files found exits upload."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        os.mkdir("cli_test_data")
        res = runner.invoke(
            upload,
            ["cli_test_data", *credentials],
        )
        assert res.exit_code == 1
        assert "No FASTQ files found in the path" in res.output
        if using_api_key:
            assert vcr.play_count == 0
        elif not recording:
            # Check that we are making just one request (to the login) if we
            # are not recording the cassette
            assert vcr.play_count == 1


@pytest.mark.vcr
@assert_authorization
def test_upload_invalid_destination(
    credentials, mocker, recording, using_api_key, vcr
):  # pylint: disable=unused-argument
    """Test that invalid destination exists upload."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        os.mkdir("cli_test_data")
        with open("cli_test_data/test.fastq.gz", "w", encoding="utf-8") as fastq_file:
            fastq_file.write("AAABBB")
        res = runner.invoke(
            upload,
            ["cli_test_data", "foobar_dir", *credentials],
        )
        assert res.exit_code == 1
        assert (
            f"Invalid destination path. Must start with '{UPLOAD_PREFIX}'" in res.output
        )
        if using_api_key:
            assert vcr.play_count == 0
        elif not recording:
            # Check that we are making just one request (to the login) if we
            # are playing the cassette
            assert vcr.play_count == 1


@pytest.mark.vcr
@assert_authorization
def test_upload_invalid_source(
    credentials, mocker, recording, using_api_key, vcr
):  # pylint: disable=unused-argument
    """Test source raises error if not a map file/directory"""
    runner = CliRunner()
    with runner.isolated_filesystem():
        os.mkdir("cli_test_data")
        with open("cli_test_data/test.fastq.gz", "w", encoding="utf-8") as fastq_file:
            fastq_file.write("ACTG")
        res = runner.invoke(
            upload,
            ["cli_test_data/test.fastq.gz", *credentials],
        )
        assert res.exit_code == 1
        assert "must be a directory or a map file" in res.output

        if using_api_key:
            assert vcr.play_count == 0
        elif not recording:
            # Check that we are making just one request (to the login) if we
            # are playing the cassette
            assert vcr.play_count == 1


@pytest.mark.vcr
@assert_authorization
def test_upload_project_id_not_uuid(
    credentials, mocker, recording, using_api_key, vcr
):  # pylint: disable=unused-argument
    """Test that project id is valid UUID when uploading."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        os.mkdir("cli_test_data")
        with open("cli_test_data/test.fastq.gz", "w", encoding="utf-8") as fastq_file:
            fastq_file.write("AAABBB")
        res = runner.invoke(
            upload,
            ["cli_test_data", "--run-project-id", "1234", *credentials],
        )

        assert res.exit_code == 1
        assert "--run-project-id is not valid" in res.output
        if using_api_key:
            assert vcr.play_count == 0
        elif not recording:
            # Check that we are making just one request (to the login) if we
            # are playing the cassette
            assert vcr.play_count == 1


@pytest.mark.vcr(
    filter_query_parameters=[("search", "gncv://cli-mock/test.fastq.gz")],
)
@assert_authorization
def test_upload_and_run_immediately(credentials, mocker, project_id, recording, vcr):
    """Upload and assign right away."""
    # pylint: disable=too-many-locals
    runner = CliRunner()
    with runner.isolated_filesystem():
        os.mkdir("cli_test_data")
        with open("cli_test_data/test.fastq.gz", "w", encoding="utf-8") as fastq_file:
            fastq_file.write("AAABBB")

        mocked_get_credentials = mocker.patch(
            "gencove.command.upload.main.get_s3_client_refreshable",
            side_effect=get_s3_client_refreshable,
        )
        mocked_upload_file = mocker.patch(
            "gencove.command.upload.main.upload_file", side_effect=upload_file
        )
        if not recording:
            # Mock get_upload credentials only if using the cassettes, since
            # we mock the return value.
            upload_details_response = get_vcr_response(
                "/api/v2/uploads-post-data/", vcr
            )
            mocked_get_upload_details = mocker.patch.object(
                APIClient,
                "get_upload_details",
                return_value=UploadsPostData(**upload_details_response),
            )
            sample_sheet_response = get_vcr_response("/api/v2/sample-sheet/", vcr)
            mocked_get_sample_sheet = mocker.patch.object(
                APIClient,
                "get_sample_sheet",
                return_value=SampleSheet(**sample_sheet_response),
            )
            project_sample_response = get_vcr_response(
                "/api/v2/project-samples/", vcr, operator.contains
            )
            mocked_assign_sample = mocker.patch.object(
                APIClient,
                "add_samples_to_project",
                return_value=UploadSamples(**project_sample_response),
            )
        mocked_regular_progress_bar = mocker.patch(
            "gencove.command.upload.main.get_regular_progress_bar",
            side_effect=get_regular_progress_bar,
        )
        res = runner.invoke(
            upload,
            ["cli_test_data", "--run-project-id", project_id, *credentials],
        )

        assert not res.exception
        assert res.exit_code == 0
        mocked_get_credentials.assert_called_once()
        mocked_upload_file.assert_called_once()
        if not recording:
            mocked_get_upload_details.assert_called_once()
            mocked_get_sample_sheet.assert_called()
            mocked_assign_sample.assert_called_once()
        mocked_regular_progress_bar.assert_called_once()


@pytest.mark.vcr
@assert_authorization
def test_upload_and_run_immediately__with_metadata(
    credentials, mocker, project_id, recording, vcr
):
    """Upload and assign right away."""
    # pylint: disable=too-many-locals
    runner = CliRunner()
    with runner.isolated_filesystem():
        os.mkdir("cli_test_data")
        with open("cli_test_data/test.fastq.gz", "w", encoding="utf-8") as fastq_file:
            fastq_file.write("AAABBB")

        mocked_get_credentials = mocker.patch(
            "gencove.command.upload.main.get_s3_client_refreshable",
            side_effect=get_s3_client_refreshable,
        )
        mocked_upload_file = mocker.patch(
            "gencove.command.upload.main.upload_file", side_effect=upload_file
        )

        mocked_regular_progress_bar = mocker.patch(
            "gencove.command.upload.main.get_regular_progress_bar",
            side_effect=get_regular_progress_bar,
        )

        if not recording:
            # Mock get_upload credentials only if using the cassettes, since
            # we mock the return value.
            upload_details_response = get_vcr_response(
                "/api/v2/uploads-post-data/", vcr
            )
            mocked_get_upload_details = mocker.patch.object(
                APIClient,
                "get_upload_details",
                return_value=UploadsPostData(**upload_details_response),
            )
            sample_sheet_response = get_vcr_response("/api/v2/sample-sheet/", vcr)
            mocked_get_sample_sheet = mocker.patch.object(
                APIClient,
                "get_sample_sheet",
                return_value=SampleSheet(**sample_sheet_response),
            )
            project_sample_response = get_vcr_response(
                "/api/v2/project-samples/", vcr, operator.contains
            )
            mocked_assign_sample = mocker.patch.object(
                APIClient,
                "add_samples_to_project",
                return_value=UploadSamples(**project_sample_response),
            )
        res = runner.invoke(
            upload,
            [
                "cli_test_data",
                "--run-project-id",
                project_id,
                "--metadata",
                "[1,2]",
                *credentials,
            ],
        )

        assert not res.exception
        assert res.exit_code == 0
        mocked_get_credentials.assert_called_once()
        mocked_upload_file.assert_called_once()
        mocked_regular_progress_bar.assert_called_once()
        if not recording:
            mocked_get_upload_details.assert_called_once()
            mocked_get_sample_sheet.assert_called()
            mocked_assign_sample.assert_called_once()


@pytest.mark.vcr
@assert_authorization
def test_upload_and_run_immediately__invalid_metadata(credentials, mocker, project_id):
    """Upload and assign right away with invalid metadata."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        os.mkdir("cli_test_data")
        with open("cli_test_data/test.fastq.gz", "w", encoding="utf-8") as fastq_file:
            fastq_file.write("AAABBB")

        mocked_get_credentials = mocker.patch(
            "gencove.command.upload.main.get_s3_client_refreshable"
        )

        mocked_get_upload_details = mocker.patch.object(
            APIClient,
            "get_upload_details",
        )
        mocked_upload_file = mocker.patch("gencove.command.upload.main.upload_file")
        mocked_get_sample_sheet = mocker.patch.object(
            APIClient,
            "get_sample_sheet",
        )
        mocked_assign_sample = mocker.patch.object(APIClient, "add_samples_to_project")

        res = runner.invoke(
            upload,
            [
                "cli_test_data",
                *credentials,
                "--run-project-id",
                project_id,
                "--metadata",
                "[1,2,3",
            ],
        )

        assert res.exit_code == 1
        mocked_get_credentials.assert_not_called()
        mocked_get_upload_details.assert_not_called()
        mocked_upload_file.assert_not_called()
        mocked_get_sample_sheet.assert_not_called()
        mocked_assign_sample.assert_not_called()
        assert "--metadata is not valid JSON" in res.output


@pytest.mark.vcr
@assert_authorization
def test_upload__with_metadata_without_project_id(credentials, mocker):
    """Test that project id is present if attaching metadata when
    uploading."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        os.mkdir("cli_test_data")
        with open("cli_test_data/test.fastq.gz", "w", encoding="utf-8") as fastq_file:
            fastq_file.write("AAABBB")

        mocked_get_credentials = mocker.patch(
            "gencove.command.upload.main.get_s3_client_refreshable"
        )
        res = runner.invoke(
            upload,
            [
                "cli_test_data",
                *credentials,
                "--metadata",
                "[1,2]",
            ],
        )

        assert res.exit_code == 1
        assert "--metadata cannot be used without --run-project-id" in res.output
        mocked_get_credentials.assert_not_called()


@pytest.mark.vcr
@assert_authorization
def test_upload_and_run_immediately_something_went_wrong(
    credentials, mocker, project_id, recording, vcr
):
    """Upload and assign right away did't work."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        os.mkdir("cli_test_data")
        with open("cli_test_data/test.fastq.gz", "w", encoding="utf-8") as fastq_file:
            fastq_file.write("AAABBB")

        mocked_get_credentials = mocker.patch(
            "gencove.command.upload.main.get_s3_client_refreshable",
            side_effect=get_s3_client_refreshable,
        )
        mocked_upload_file = mocker.patch(
            "gencove.command.upload.main.upload_file", side_effect=upload_file
        )
        if not recording:
            # Mock get_upload credentials only if using the cassettes, since
            # we mock the return value.
            upload_details_response = get_vcr_response(
                "/api/v2/uploads-post-data/", vcr
            )
            mocked_get_upload_details = mocker.patch.object(
                APIClient,
                "get_upload_details",
                return_value=UploadsPostData(**upload_details_response),
            )
        mocked_get_sample_sheet = mocker.patch.object(
            APIClient,
            "get_sample_sheet",
            return_value=SampleSheet(**{"meta": {"next": None}, "results": []}),
        )
        mocked_assign_sample = mocker.patch.object(APIClient, "add_samples_to_project")

        res = runner.invoke(
            upload,
            [
                "cli_test_data",
                *credentials,
                "--run-project-id",
                project_id,
            ],
        )

        assert res.exit_code == 0
        mocked_get_credentials.assert_called_once()
        if not recording:
            mocked_get_upload_details.assert_called_once()
        mocked_upload_file.assert_called_once()
        mocked_get_sample_sheet.assert_called()
        mocked_assign_sample.assert_not_called()


@pytest.mark.vcr
@assert_authorization
def test_upload_and_run_immediately_with_output_to_file(
    credentials, mocker, project_id, recording, vcr
):
    """Upload and assign right away, then save results to a file."""
    # pylint: disable=too-many-locals
    runner = CliRunner()
    with runner.isolated_filesystem():
        os.mkdir("cli_test_data")
        with open("cli_test_data/test.fastq.gz", "w", encoding="utf-8") as fastq_file:
            fastq_file.write("AAABBB")

        mocked_get_credentials = mocker.patch(
            "gencove.command.upload.main.get_s3_client_refreshable",
            side_effect=get_s3_client_refreshable,
        )
        mocked_upload_file = mocker.patch(
            "gencove.command.upload.main.upload_file", side_effect=upload_file
        )

        mocked_regular_progress_bar = mocker.patch(
            "gencove.command.upload.main.get_regular_progress_bar",
            side_effect=get_regular_progress_bar,
        )

        if not recording:
            # Mock get_upload credentials only if using the cassettes, since
            # we mock the return value.
            upload_details_response = get_vcr_response(
                "/api/v2/uploads-post-data/", vcr
            )
            mocked_get_upload_details = mocker.patch.object(
                APIClient,
                "get_upload_details",
                return_value=UploadsPostData(**upload_details_response),
            )
            sample_sheet_response = get_vcr_response("/api/v2/sample-sheet/", vcr)
            mocked_get_sample_sheet = mocker.patch.object(
                APIClient,
                "get_sample_sheet",
                return_value=SampleSheet(**sample_sheet_response),
            )
            project_sample_response = get_vcr_response(
                "/api/v2/project-samples/", vcr, operator.contains
            )
            mocked_assign_sample = mocker.patch.object(
                APIClient,
                "add_samples_to_project",
                return_value=UploadSamples(**project_sample_response),
            )
        res = runner.invoke(
            upload,
            [
                "cli_test_data",
                *credentials,
                "--run-project-id",
                project_id,
                "--output",
                "samples.json",
            ],
        )

        assert not res.exception
        assert res.exit_code == 0
        mocked_get_credentials.assert_called_once()
        mocked_upload_file.assert_called_once()
        mocked_regular_progress_bar.assert_called_once()

        if not recording:
            mocked_get_upload_details.assert_called_once()
            mocked_get_sample_sheet.assert_called()
            mocked_assign_sample.assert_called_once()
            with open("samples.json", "r", encoding="utf-8") as output_file:
                output_content = output_file.read()
            # r2 fastq key is not present on the file
            assert project_sample_response["uploads"][0]["fastq"]["r2"] is None
            del project_sample_response["uploads"][0]["fastq"]["r2"]
            assert (
                json.dumps(project_sample_response["uploads"], indent=4)
                == output_content
            )


@pytest.mark.vcr
@assert_authorization
def test_upload_and_run_immediately_with_output_to_nested_file(
    credentials, mocker, project_id, recording, vcr
):
    """Upload and assign right away, then save results to a file."""
    # pylint: disable=too-many-locals
    runner = CliRunner()
    with runner.isolated_filesystem():
        os.mkdir("cli_test_data")
        with open("cli_test_data/test.fastq.gz", "w", encoding="utf-8") as fastq_file:
            fastq_file.write("AAABBB")

        mocked_get_credentials = mocker.patch(
            "gencove.command.upload.main.get_s3_client_refreshable",
            side_effect=get_s3_client_refreshable,
        )
        mocked_upload_file = mocker.patch(
            "gencove.command.upload.main.upload_file", side_effect=upload_file
        )

        mocked_regular_progress_bar = mocker.patch(
            "gencove.command.upload.main.get_regular_progress_bar",
            side_effect=get_regular_progress_bar,
        )

        if not recording:
            # Mock get_upload credentials only if using the cassettes, since
            # we mock the return value.
            upload_details_response = get_vcr_response(
                "/api/v2/uploads-post-data/", vcr
            )
            mocked_get_upload_details = mocker.patch.object(
                APIClient,
                "get_upload_details",
                return_value=UploadsPostData(**upload_details_response),
            )
            sample_sheet_response = get_vcr_response("/api/v2/sample-sheet/", vcr)
            mocked_get_sample_sheet = mocker.patch.object(
                APIClient,
                "get_sample_sheet",
                return_value=SampleSheet(**sample_sheet_response),
            )
            project_sample_response = get_vcr_response(
                "/api/v2/project-samples/", vcr, operator.contains
            )
            mocked_assign_sample = mocker.patch.object(
                APIClient,
                "add_samples_to_project",
                return_value=UploadSamples(**project_sample_response),
            )
        res = runner.invoke(
            upload,
            [
                "cli_test_data",
                *credentials,
                "--run-project-id",
                project_id,
                "--output",
                "somefolder/samples.json",
            ],
        )

        assert res.exit_code == 0
        mocked_get_credentials.assert_called_once()
        mocked_upload_file.assert_called_once()
        mocked_regular_progress_bar.assert_called_once()

        if not recording:
            mocked_get_upload_details.assert_called_once()
            mocked_get_sample_sheet.assert_called()
            mocked_assign_sample.assert_called_once()
            with open("somefolder/samples.json", "r", encoding="utf-8") as output_file:
                output_content = output_file.read()
            # r2 fastq key is not present on the file
            assert project_sample_response["uploads"][0]["fastq"]["r2"] is None
            del project_sample_response["uploads"][0]["fastq"]["r2"]
            assert (
                json.dumps(project_sample_response["uploads"], indent=4)
                == output_content
            )


@pytest.mark.vcr
@assert_authorization
def test_upload_and_run_immediately_with_stdout(
    credentials, mocker, project_id, recording, vcr
):
    """Upload and assign right away, then print out the results."""
    # pylint: disable=too-many-locals
    runner = CliRunner()
    with runner.isolated_filesystem():
        os.mkdir("cli_test_data")
        with open("cli_test_data/test.fastq.gz", "w", encoding="utf-8") as fastq_file:
            fastq_file.write("AAABBB")

        mocked_get_credentials = mocker.patch(
            "gencove.command.upload.main.get_s3_client_refreshable",
            side_effect=get_s3_client_refreshable,
        )

        if not recording:
            # Mock get_upload credentials only if using the cassettes, since
            # we mock the return value.
            upload_details_response = get_vcr_response(
                "/api/v2/uploads-post-data/", vcr
            )
            mocked_get_upload_details = mocker.patch.object(
                APIClient,
                "get_upload_details",
                return_value=UploadsPostData(**upload_details_response),
            )
            sample_sheet_response = get_vcr_response("/api/v2/sample-sheet/", vcr)
            mocked_get_sample_sheet = mocker.patch.object(
                APIClient,
                "get_sample_sheet",
                return_value=SampleSheet(**sample_sheet_response),
            )
            project_sample_response = get_vcr_response(
                "/api/v2/project-samples/", vcr, operator.contains
            )
            mocked_assign_sample = mocker.patch.object(
                APIClient,
                "add_samples_to_project",
                return_value=UploadSamples(**project_sample_response),
            )
            # These mocks needs to be here and without side effect otherwise
            # a weird behavior on the stdout will happend and the test fails.
            mocked_upload_file = mocker.patch("gencove.command.upload.main.upload_file")

            mocker.patch(
                "gencove.command.upload.main.get_regular_progress_bar",
            )

        res = runner.invoke(
            upload,
            [
                "cli_test_data",
                *credentials,
                "--run-project-id",
                project_id,
                "--output",
                "-",
            ],
        )

        assert res.exit_code == 0

        mocked_get_credentials.assert_called_once()
        if not recording:
            mocked_upload_file.assert_called_once()
            mocked_get_upload_details.assert_called_once()
            mocked_get_sample_sheet.assert_called()
            mocked_assign_sample.assert_called_once()
            # r2 fastq key is not present on the file
            assert project_sample_response["uploads"][0]["fastq"]["r2"] is None
            del project_sample_response["uploads"][0]["fastq"]["r2"]
            assert (
                json.dumps(project_sample_response["uploads"], indent=4) in res.output
            )


@pytest.mark.vcr
@assert_authorization
def test_upload_without_progressbar(credentials, mocker, recording, vcr):
    """Upload do not show the progress bar."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        os.mkdir("cli_test_data")
        with open("cli_test_data/test.fastq.gz", "w", encoding="utf-8") as fastq_file:
            fastq_file.write("AAABBB")

        mocked_get_credentials = mocker.patch(
            "gencove.command.upload.main.get_s3_client_refreshable",
            side_effect=get_s3_client_refreshable,
        )
        mocked_upload_file = mocker.patch("gencove.command.upload.main.upload_file")
        if not recording:
            # Mock get_upload_details only if using the cassettes, since
            # we mock the return value.
            upload_details_response = get_vcr_response(
                "/api/v2/uploads-post-data/", vcr
            )
            mocked_get_upload_details = mocker.patch.object(
                APIClient,
                "get_upload_details",
                return_value=UploadsPostData(**upload_details_response),
            )

        res = runner.invoke(
            upload,
            [
                "cli_test_data",
                *credentials,
                "--no-progress",
            ],
        )

        assert res.exit_code == 0
        mocked_get_credentials.assert_called_once()
        mocked_upload_file.assert_called_once()
        assert mocked_upload_file.call_args[1]["no_progress"]
        if not recording:
            mocked_get_upload_details.assert_called_once()


@pytest.mark.vcr
@assert_authorization
def test_upload_and_run_immediately_without_progressbar(
    credentials, mocker, project_id, recording, vcr
):
    """Upload and assign right away."""
    # pylint: disable=too-many-locals
    runner = CliRunner()
    with runner.isolated_filesystem():
        os.mkdir("cli_test_data")
        with open("cli_test_data/test.fastq.gz", "w", encoding="utf-8") as fastq_file:
            fastq_file.write("AAABBB")

        mocked_get_credentials = mocker.patch(
            "gencove.command.upload.main.get_s3_client_refreshable",
            side_effect=get_s3_client_refreshable,
        )
        mocked_upload_file = mocker.patch(
            "gencove.command.upload.main.upload_file", side_effect=upload_file
        )

        mocked_regular_progress_bar = mocker.patch(
            "gencove.command.upload.main.get_regular_progress_bar",
            side_effect=get_regular_progress_bar,
        )
        if not recording:
            # Mock get_upload credentials only if using the cassettes, since
            # we mock the return value.
            upload_details_response = get_vcr_response(
                "/api/v2/uploads-post-data/", vcr
            )
            mocked_get_upload_details = mocker.patch.object(
                APIClient,
                "get_upload_details",
                return_value=UploadsPostData(**upload_details_response),
            )
            sample_sheet_response = get_vcr_response("/api/v2/sample-sheet/", vcr)
            mocked_get_sample_sheet = mocker.patch.object(
                APIClient,
                "get_sample_sheet",
                return_value=SampleSheet(**sample_sheet_response),
            )
            project_sample_response = get_vcr_response(
                "/api/v2/project-samples/", vcr, operator.contains
            )
            mocked_assign_sample = mocker.patch.object(
                APIClient,
                "add_samples_to_project",
                return_value=UploadSamples(**project_sample_response),
            )

        res = runner.invoke(
            upload,
            [
                "cli_test_data",
                *credentials,
                "--run-project-id",
                project_id,
                "--no-progress",
            ],
        )

        assert res.exit_code == 0
        mocked_get_credentials.assert_called_once()
        mocked_upload_file.assert_called_once()
        mocked_regular_progress_bar.assert_not_called()

        if not recording:
            mocked_get_upload_details.assert_called_once()
            mocked_get_sample_sheet.assert_called()
            mocked_assign_sample.assert_called_once()


@pytest.mark.vcr
@assert_authorization
def test_upload_and_run_immediately_slow_response_retry(
    credentials, mocker, project_id, recording, vcr
):
    """Upload and assign right away and retry on slow response."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        os.mkdir("cli_test_data")
        with open("cli_test_data/test.fastq.gz", "w", encoding="utf-8") as fastq_file:
            fastq_file.write("AAABBB")

        mocked_get_credentials = mocker.patch(
            "gencove.command.upload.main.get_s3_client_refreshable",
            side_effect=get_s3_client_refreshable,
        )
        mocked_upload_file = mocker.patch(
            "gencove.command.upload.main.upload_file", side_effect=upload_file
        )
        if not recording:
            # Mock get_upload credentials only if using the cassettes, since
            # we mock the return value.
            upload_details_response = get_vcr_response(
                "/api/v2/uploads-post-data/", vcr
            )
            mocked_get_upload_details = mocker.patch.object(
                APIClient,
                "get_upload_details",
                return_value=UploadsPostData(**upload_details_response),
            )
        mocked_get_sample_sheet = mocker.patch.object(
            APIClient,
            "get_sample_sheet",
            side_effect=APIClientTimeout("Could not connect to the api server"),
        )

        res = runner.invoke(
            upload,
            [
                "cli_test_data",
                *credentials,
                "--run-project-id",
                project_id,
                "--no-progress",
            ],
        )

        assert res.exit_code == 0
        mocked_get_credentials.assert_called_once()
        mocked_upload_file.assert_called_once()
        if not recording:
            mocked_get_upload_details.assert_called_once()
        assert mocked_get_sample_sheet.call_count == 5
        assert "there was an error automatically running them" in res.output


def test_upload_retry_after_unauthorized(mocker):
    """Test that the upload is performed when retrying due to unauthorized
    http response.
    """
    runner = CliRunner()
    with runner.isolated_filesystem():
        os.mkdir("cli_test_data")
        with open("cli_test_data/test.fastq.gz", "w", encoding="utf-8") as fastq_file:
            fastq_file.write("AAABBB")

        def _login(
            self, email, password, otp_token=None
        ):  # pylint: disable=unused-argument
            # pylint: disable=protected-access
            self._jwt_refresh_token = "refresh_token"

        mocked_login = mocker.patch.object(
            APIClient, "login", side_effect=_login, autospec=True
        )

        force_refresh_jwt = True

        def _request(
            endpoint,
            *args,  # pylint: disable=unused-argument
            **kwargs,  # pylint: disable=unused-argument
        ):
            if ApiEndpoints.UPLOAD_DETAILS.value == endpoint:
                nonlocal force_refresh_jwt
                if force_refresh_jwt:
                    force_refresh_jwt = False
                    raise APIClientError("Test error.", 401)
                return {
                    "id": str(uuid4()),
                    "last_status": {"id": str(uuid4()), "status": ""},
                    "s3": {"bucket": "test", "object_name": "test"},
                }
            if ApiEndpoints.REFRESH_JWT.value == endpoint:
                return {"access": ""}
            return {}

        mocked_request = mocker.patch.object(
            APIClient, "_request", side_effect=_request
        )

        mocked_get_credentials = mocker.patch(
            "gencove.command.upload.main.get_s3_client_refreshable"
        )

        res = runner.invoke(
            upload,
            ["cli_test_data"],
            input="\n".join(["foo@bar.com", "123456"]),
        )

        assert res.exit_code == 0
        mocked_login.assert_called_once()
        mocked_get_credentials.assert_called_once()
        # Call count = upload details + refresh jwt + retry upload details
        assert mocked_request.call_count == 3
        assert force_refresh_jwt is False
