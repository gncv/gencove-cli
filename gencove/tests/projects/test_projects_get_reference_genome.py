"""Test project's get reference genome command."""
# pylint: disable=import-error, wrong-import-order

import os
from unittest.mock import call
from uuid import uuid4

from click.testing import CliRunner

from gencove.command.download.utils import download_file
from gencove.command.projects.get_reference_genome.cli import get_reference_genome
from gencove.models import SampleFile
from gencove.tests.decorators import assert_authorization, assert_no_requests
from gencove.tests.filters import (
    filter_aws_headers,
    filter_file_types_request,
    filter_jwt,
    mock_binary_response,
    replace_gencove_url_vcr,
    replace_s3_from_url,
)
from gencove.tests.projects.vcr.filters import (
    filter_projects_detail_request,
    filter_projects_detail_response,
)
from gencove.tests.upload.vcr.filters import filter_volatile_dates
from gencove.tests.utils import MOCK_UUID

import pytest

from vcr import VCR


@pytest.fixture(scope="module")
def vcr_config():
    """VCR configuration."""
    return {
        "cassette_library_dir": "gencove/tests/projects/vcr/get_reference_genome",
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
            filter_projects_detail_request,
            replace_s3_from_url,
        ],
        "before_record_response": [
            filter_jwt,
            filter_volatile_dates,
            mock_binary_response,
            filter_aws_headers,
            filter_projects_detail_response,
        ],
    }


@assert_no_requests
def test_no_required_options(credentials, mocker):  # pylint: disable=unused-argument
    """Test that command exits without project id provided."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        os.mkdir("cli_test_data")
        res = runner.invoke(
            get_reference_genome,
            [
                "22",
                "cli_test_data",
                *credentials,
            ],
        )
        assert res.exit_code == 1
        assert "ERROR: Project ID is not valid. Exiting." in res.output


@pytest.mark.vcr
@assert_authorization
def test_get_reference_genome__not_owned_project(
    credentials, mocker
):  # pylint: disable=unused-argument
    """Test get reference genome fails when project is not owned."""
    runner = CliRunner()
    #
    project_id = str(uuid4())
    with runner.isolated_filesystem():
        os.mkdir("cli_test_data")
        res = runner.invoke(
            get_reference_genome,
            [
                project_id,
                "cli_test_data",
                *credentials,
            ],
        )
    assert res.exit_code == 1
    assert "WARNING: There was an error while validating file types." in res.output
    assert f"ERROR: Project {project_id} does not exist." in res.output


@pytest.mark.vcr
@assert_authorization
@pytest.mark.parametrize("remove_hyphens", [True, False])
def test_get_reference_genome__success(  # pylint: disable=too-many-arguments
    credentials, mocker, project_id_reference_genome, recording, remove_hyphens
):
    """Test get reference genome success."""
    mocked_download_file = mocker.patch(
        "gencove.command.projects.get_reference_genome.main.download_file",
        side_effect=download_file,
    )
    runner = CliRunner()
    if remove_hyphens:
        project_id_reference_genome = project_id_reference_genome.replace("-", "")
    with runner.isolated_filesystem():
        os.mkdir("cli_test_data")
        res = runner.invoke(
            get_reference_genome,
            [
                project_id_reference_genome,
                "cli_test_data",
                *credentials,
            ],
        )
        assert res.exit_code == 0
    assert mocked_download_file.call_count == 10
    if not recording:
        file_types = [
            ("genome-dict", "dict"),
            ("genome-fasta", "fasta.gz"),
            ("genome-fasta_amb", "fasta.gz.amb"),
            ("genome-fasta_ann", "fasta.gz.ann"),
            ("genome-fasta_bwt", "fasta.gz.bwt"),
            ("genome-fasta_fai", "fasta.gz.fai"),
            ("genome-fasta_gzi", "fasta.gz.gzi"),
            ("genome-fasta_pac", "fasta.gz.pac"),
            ("genome-fasta_sa", "fasta.gz.sa"),
            ("genome-fasta_vcf_header", "fasta.gz.vcf_header"),
        ]

        calls = []
        for file_type, extension in file_types:
            filename = f"{MOCK_UUID}_{file_type}.{extension}"
            query_param = (
                f"response-content-disposition=attachment%3B+filename%3D{filename}"
            )
            download_url = f"https://example.com/genome.{extension}?{query_param}"
            calls.append(
                call(
                    f"cli_test_data/{filename}",
                    # We need to use SampleFile to have a full HttpUrl pydantic
                    # attribute
                    SampleFile(id=MOCK_UUID, download_url=download_url).download_url,
                    no_progress=False,
                )
            )
        mocked_download_file.assert_has_calls(calls, any_order=True)


# pylint: disable=too-many-arguments
@pytest.mark.vcr
@assert_authorization
def test_get_reference_genome__success_specific_file_type(
    credentials, mocker, project_id_reference_genome, recording
):
    """Test get reference genome success specifying file types."""
    mocked_download_file = mocker.patch(
        "gencove.command.projects.get_reference_genome.main.download_file",
        side_effect=download_file,
    )
    runner = CliRunner()
    with runner.isolated_filesystem():
        os.mkdir("cli_test_data")
        res = runner.invoke(
            get_reference_genome,
            [
                project_id_reference_genome,
                "cli_test_data",
                "--file-types",
                "genome-dict",
                *credentials,
            ],
        )
        assert res.exit_code == 0
    assert mocked_download_file.call_count == 1
    if not recording:
        filename = f"{MOCK_UUID}_genome-dict.dict"
        query_param = (
            f"response-content-disposition=attachment%3B+filename%3D{filename}"
        )
        download_url = f"https://example.com/genome.dict?{query_param}"
        mocked_download_file.assert_called_once_with(
            f"cli_test_data/{filename}",
            SampleFile(
                id=MOCK_UUID,
                download_url=download_url,
            ).download_url,
            no_progress=False,
        )


# pylint: disable=too-many-arguments
@pytest.mark.vcr
@assert_authorization
def test_get_reference_genome__success_no_progress(
    credentials, mocker, project_id_reference_genome, recording
):
    """Test command doesn't show progress bar."""
    mocked_download_file = mocker.patch(
        "gencove.command.projects.get_reference_genome.main.download_file",
        side_effect=download_file,
    )
    runner = CliRunner()
    with runner.isolated_filesystem():
        os.mkdir("cli_test_data")
        res = runner.invoke(
            get_reference_genome,
            [
                project_id_reference_genome,
                "cli_test_data",
                "--file-types",
                "genome-dict",
                *credentials,
                "--no-progress",
            ],
        )
        assert res.exit_code == 0
    assert mocked_download_file.call_count == 1
    if not recording:
        filename = f"{MOCK_UUID}_genome-dict.dict"
        query_param = (
            f"response-content-disposition=attachment%3B+filename%3D{filename}"
        )
        download_url = f"https://example.com/genome.dict?{query_param}"
        mocked_download_file.assert_called_once_with(
            f"cli_test_data/{filename}",
            SampleFile(
                id=MOCK_UUID,
                download_url=download_url,
            ).download_url,
            no_progress=True,
        )


@pytest.mark.vcr
@assert_authorization
def test_get_reference_genome__bad_file_type(  # pylint: disable=too-many-arguments
    credentials, mocker, project_id_reference_genome
):
    """Fails when an invalid file type is provided."""
    mocked_download_file = mocker.patch(
        "gencove.command.projects.get_reference_genome.main.download_file",
        side_effect=download_file,
    )
    runner = CliRunner()
    with runner.isolated_filesystem():
        os.mkdir("cli_test_data")
        res = runner.invoke(
            get_reference_genome,
            [
                project_id_reference_genome,
                "cli_test_data",
                "--file-types",
                "bad-file-type",
                *credentials,
            ],
        )
        assert res.exit_code == 1
        assert "Invalid file types: bad-file-type." in res.output
        assert (
            "Run 'gencove file-types --object reference-genome' command for a list of "
            "valid file types. " in res.output
        )
    mocked_download_file.assert_not_called()
