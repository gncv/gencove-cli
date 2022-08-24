"""Test create merged project's VCF file command."""

import io
import sys
from uuid import uuid4

from click import echo
from click.testing import CliRunner

from gencove.client import APIClient, APIClientError  # noqa: I100
from gencove.command.projects.cli import create_merged_vcf
from gencove.models import ProjectMergeVCFs


def test_create_merged_vcf__bad_project_id(mocker):
    """Test create merged file failure when non-uuid string is used as
    project id.
    """
    runner = CliRunner()

    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_create_merged_vcf = mocker.patch.object(
        APIClient,
        "create_merged_vcf",
        return_value=ProjectMergeVCFs(id=uuid4()),
    )

    res = runner.invoke(
        create_merged_vcf,
        [
            "1111111",
            "--email",
            "foo@bar.com",
            "--password",
            "123",
        ],
    )

    assert res.exit_code == 1
    mocked_login.assert_called_once()
    mocked_create_merged_vcf.assert_not_called()
    assert "Project ID is not valid" in res.output


def test_create_merged_vcf__not_owned_project(mocker):
    """Test create merged file failure when project is not owned."""
    mocked_response = {"detail": "Not found."}

    runner = CliRunner()

    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_create_merged_vcf = mocker.patch.object(
        APIClient,
        "create_merged_vcf",
        return_value=mocked_response,
        side_effect=APIClientError(message="", status_code=403),
    )

    res = runner.invoke(
        create_merged_vcf,
        [
            str(uuid4()),
            "--email",
            "foo@bar.com",
            "--password",
            "123",
        ],
    )

    assert res.exit_code == 1
    mocked_login.assert_called_once()
    mocked_create_merged_vcf.assert_called_once()
    assert "You do not have the sufficient permission" in res.output


def test_create_merged_vcf__already_running(mocker):
    """Test create merged file failure when the job is alredy running."""
    project_id = str(uuid4())
    message = f"Merge VCFs for project {project_id} is already running"
    mocked_response = [message]

    runner = CliRunner()

    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_create_merged_vcf = mocker.patch.object(
        APIClient,
        "create_merged_vcf",
        return_value=mocked_response,
        side_effect=APIClientError(message=message, status_code=400),
    )

    res = runner.invoke(
        create_merged_vcf,
        [
            project_id,
            "--email",
            "foo@bar.com",
            "--password",
            "123",
        ],
    )

    assert res.exit_code == 1
    mocked_login.assert_called_once()
    mocked_create_merged_vcf.assert_called_once()
    assert "is already running" in res.output


def test_create_merged_vcf__not_able(mocker):
    """Test create merged file failure when it cannot be done."""
    project_id = str(uuid4())
    mocked_response = ["You attempted to merge VCFs for a project that cannot do that"]

    runner = CliRunner()

    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_create_merged_vcf = mocker.patch.object(
        APIClient,
        "create_merged_vcf",
        return_value=mocked_response,
        side_effect=APIClientError(message=mocked_response[0], status_code=400),
    )

    res = runner.invoke(
        create_merged_vcf,
        [
            project_id,
            "--email",
            "foo@bar.com",
            "--password",
            "123",
        ],
    )

    assert res.exit_code == 1
    mocked_login.assert_called_once()
    mocked_create_merged_vcf.assert_called_once()
    assert "You attempted to merge VCFs for a project that cannot do that" in res.output


def test_create_merged_vcf__no_samples(mocker):
    """Test create merged file failure when there are no samples."""
    project_id = str(uuid4())
    mocked_response = ["No samples found in project"]

    runner = CliRunner()

    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_create_merged_vcf = mocker.patch.object(
        APIClient,
        "create_merged_vcf",
        return_value=mocked_response,
        side_effect=APIClientError(message=mocked_response[0], status_code=400),
    )

    res = runner.invoke(
        create_merged_vcf,
        [
            project_id,
            "--email",
            "foo@bar.com",
            "--password",
            "123",
        ],
    )

    assert res.exit_code == 1
    mocked_login.assert_called_once()
    mocked_create_merged_vcf.assert_called_once()
    assert "No samples found in project" in res.output


def test_create_merged_vcf__up_to_date(mocker):
    """Test create merged file failure when attempting to create another one
    that is the same.
    """

    project_id = str(uuid4())
    message = f"Merged VCF file for project {project_id} is up-to-date"
    mocked_response = [message]

    runner = CliRunner()

    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_create_merged_vcf = mocker.patch.object(
        APIClient,
        "create_merged_vcf",
        return_value=mocked_response,
        side_effect=APIClientError(message=message, status_code=400),
    )

    res = runner.invoke(
        create_merged_vcf,
        [
            project_id,
            "--email",
            "foo@bar.com",
            "--password",
            "123",
        ],
    )

    assert res.exit_code == 1
    mocked_login.assert_called_once()
    mocked_create_merged_vcf.assert_called_once()
    assert "is up-to-date" in res.output


def test_create_merged_vcf__needs_two_samples(mocker):
    """Test create merged file failure when there's only one sample."""
    project_id = str(uuid4())
    mocked_response = ["should have at least 2 samples"]

    runner = CliRunner()

    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_create_merged_vcf = mocker.patch.object(
        APIClient,
        "create_merged_vcf",
        return_value=mocked_response,
        side_effect=APIClientError(message=mocked_response[0], status_code=400),
    )

    res = runner.invoke(
        create_merged_vcf,
        [
            project_id,
            "--email",
            "foo@bar.com",
            "--password",
            "123",
        ],
    )

    assert res.exit_code == 1
    mocked_login.assert_called_once()
    mocked_create_merged_vcf.assert_called_once()
    assert "should have at least 2 samples" in res.output


def test_create_merged_vcf__no_impute_files(mocker):
    """Test create merged file failure when there are no impute files."""
    project_id = str(uuid4())
    mocked_response = ["must have impute VCF files associated"]

    runner = CliRunner()

    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_create_merged_vcf = mocker.patch.object(
        APIClient,
        "create_merged_vcf",
        return_value=mocked_response,
        side_effect=APIClientError(message=mocked_response[0], status_code=400),
    )

    res = runner.invoke(
        create_merged_vcf,
        [
            project_id,
            "--email",
            "foo@bar.com",
            "--password",
            "123",
        ],
    )

    assert res.exit_code == 1
    mocked_login.assert_called_once()
    mocked_create_merged_vcf.assert_called_once()
    assert "must have impute VCF files associated" in res.output


def test_create_merged_vcf__success(mocker):
    """Test create merged file success."""
    project_id = str(uuid4())
    mocked_response = {
        "id": project_id,
        "created": "2020-09-14T08:59:00.480+00:00",
        "user": str(uuid4()),
        "last_status": {
            "id": str(uuid4()),
            "status": "running",
            "note": "",
            "created": "2020-07-28T12:46:22.719862+00:00",
        },
        "up_to_date": False,
    }

    runner = CliRunner()

    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_create_merged_vcf = mocker.patch.object(
        APIClient,
        "create_merged_vcf",
        return_value=ProjectMergeVCFs(**mocked_response),
    )

    res = runner.invoke(
        create_merged_vcf,
        [
            project_id,
            "--email",
            "foo@bar.com",
            "--password",
            "123",
        ],
    )

    assert res.exit_code == 0
    mocked_login.assert_called_once()
    mocked_create_merged_vcf.assert_called_once()
    output_line = io.BytesIO()
    sys.stdout = output_line
    echo(
        "\t".join(
            [
                mocked_response["id"],
                mocked_response["last_status"]["created"],
                mocked_response["last_status"]["status"],
            ]
        )
    )
    assert output_line.getvalue() in res.output.encode()
    assert f"Issued merge request for project {project_id}" in res.output
