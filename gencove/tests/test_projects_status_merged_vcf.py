"""Test project's status merged VCF command."""

import io
import sys
from uuid import uuid4

from click import echo
from click.testing import CliRunner

from gencove.client import APIClient, APIClientError, APIClientTimeout
from gencove.command.projects.cli import status_merged_vcf


def test_status_merged_vcf__bad_project_id(mocker):
    """Test status merged file failure when non-uuid string is used as
    project id.
    """
    runner = CliRunner()

    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_retrieve_merged_vcf = mocker.patch.object(
        APIClient,
        "retrieve_merged_vcf",
    )

    res = runner.invoke(
        status_merged_vcf,
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
    mocked_retrieve_merged_vcf.assert_not_called()
    assert "Project ID is not valid" in res.output


def test_status_merged_vcf__empty(mocker):
    """Test create merged file failure when project is responding empty.
    This can be due to no merged files or no permission required for the
    project or no project at all."""
    project_id = str(uuid4())
    mocked_response = {"detail": "Not found."}

    runner = CliRunner()

    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_retrieve_merged_vcf = mocker.patch.object(
        APIClient,
        "retrieve_merged_vcf",
        return_value=mocked_response,
        side_effect=APIClientError(message="", status_code=404),
    )

    res = runner.invoke(
        status_merged_vcf,
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
    mocked_retrieve_merged_vcf.assert_called_once()
    message = (
        "Project {} does not exist or you do not have "
        "permission required to access it or there are no "
        "running jobs associated with it.".format(project_id)
    )
    assert message in res.output


def test_status_merged_vcf__not_able(mocker):
    """Test status merged file failure when it cannot be done."""
    project_id = str(uuid4())
    mocked_response = [
        "You attempted to merge VCFs for a project that cannot do that"
    ]

    runner = CliRunner()

    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_retrieve_merged_vcf = mocker.patch.object(
        APIClient,
        "retrieve_merged_vcf",
        return_value=mocked_response,
        side_effect=APIClientError(
            message=mocked_response[0], status_code=400
        ),
    )

    res = runner.invoke(
        status_merged_vcf,
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
    mocked_retrieve_merged_vcf.assert_called_once()
    assert (
        "You attempted to merge VCFs for a project that cannot do that"
        in res.output
    )


def test_status_merged_vcf__success_but_job_failed(mocker):
    """Test status merged VCF success, but the job is in the failed state."""
    project_id = str(uuid4())
    mocked_response = {
        "id": project_id,
        "created": "2020-09-14T08:59:00.480Z",
        "user": str(uuid4()),
        "last_status": {
            "id": str(uuid4()),
            "status": "failed",
            "note": "",
            "created": "2020-07-28T12:46:22.719862Z",
        },
        "up_to_date": False,
    }

    runner = CliRunner()

    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_retrieve_merged_vcf = mocker.patch.object(
        APIClient, "retrieve_merged_vcf", return_value=mocked_response
    )

    res = runner.invoke(
        status_merged_vcf,
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
    mocked_retrieve_merged_vcf.assert_called_once()
    assert "WARNING: The job failed merging." in res.output


def test_status_merged_vcf__slow_response_retry(mocker):
    """Test status merged VCF slow response retry."""
    project_id = str(uuid4())

    runner = CliRunner()

    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_retrieve_merged_vcf = mocker.patch.object(
        APIClient,
        "retrieve_merged_vcf",
        side_effect=APIClientTimeout("Could not connect to the api server"),
    )

    res = runner.invoke(
        status_merged_vcf,
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
    assert mocked_retrieve_merged_vcf.call_count == 5


def test_status_merged_vcf__success(mocker):
    """Test status merged VCF success."""
    project_id = str(uuid4())
    mocked_response = {
        "id": project_id,
        "created": "2020-09-14T08:59:00.480Z",
        "user": str(uuid4()),
        "last_status": {
            "id": str(uuid4()),
            "status": "success",
            "note": "",
            "created": "2020-07-28T12:46:22.719862Z",
        },
        "up_to_date": False,
    }

    runner = CliRunner()

    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_retrieve_merged_vcf = mocker.patch.object(
        APIClient, "retrieve_merged_vcf", return_value=mocked_response
    )

    res = runner.invoke(
        status_merged_vcf,
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
    mocked_retrieve_merged_vcf.assert_called_once()
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
