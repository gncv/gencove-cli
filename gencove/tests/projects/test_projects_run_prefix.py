"""Test project's run prefix command."""

import copy
from uuid import uuid4

from click.testing import CliRunner

from gencove.client import (
    APIClient,
    APIClientError,
)  # noqa: I100
from gencove.command.projects.cli import run_prefix
from gencove.models import SampleSheet, UploadSamples

MOCKED_UPLOADS = dict(
    meta=dict(next=None),
    results=[
        {
            "client_id": "clientid1",
            "fastq": {
                "r1": {
                    "upload": str(uuid4()),
                    "destination_path": "gncv://batch1/clientid1_R1.fastq.gz",
                    "last_status": {
                        "id": str(uuid4()),
                        "status": "unassigned",
                    },
                },
                "r2": {
                    "upload": str(uuid4()),
                    "destination_path": "gncv://batch1/clientid1_R2.fastq.gz",
                    "last_status": {
                        "id": str(uuid4()),
                        "status": "unassigned",
                    },
                },
            },
        },
        {
            "client_id": "clientid2",
            "fastq": {
                "r1": {
                    "upload": str(uuid4()),
                    "destination_path": "gncv://batch2/clientid2_R1.fastq.gz",
                    "last_status": {
                        "id": str(uuid4()),
                        "status": "assigned",
                    },
                }
            },
        },
    ],
)

MOCKED_EMPTY_UPLOADS = dict(
    meta=dict(next=None),
    results=[],
)


def test_run_prefix__bad_project_id(mocker):
    """Test run prefix when non-uuid string is used as project
    id."""
    runner = CliRunner()
    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_get_sample_sheet = mocker.patch.object(
        APIClient,
        "get_sample_sheet",
    )
    res = runner.invoke(
        run_prefix,
        [
            "1111111",
            "gncv://batch",
            "--email",
            "foo@bar.com",
            "--password",
            "123",
        ],
    )
    assert res.exit_code == 1
    mocked_login.assert_called_once()
    mocked_get_sample_sheet.assert_not_called()
    assert "Project ID is not valid" in res.output


def test_run_prefix__bad_prefix(mocker):
    """Test run prefix when bad prefix string is used."""
    runner = CliRunner()
    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_get_sample_sheet = mocker.patch.object(
        APIClient,
        "get_sample_sheet",
    )
    res = runner.invoke(
        run_prefix,
        [
            str(uuid4()),
            "prefix://path",
            "--email",
            "foo@bar.com",
            "--password",
            "123",
        ],
    )
    assert res.exit_code == 1
    mocked_login.assert_called_once()
    mocked_get_sample_sheet.assert_not_called()
    assert "Prefix is not valid" in res.output


def test_run_prefix__bad_json(mocker):
    """Test run prefix when bad JSON is used."""
    runner = CliRunner()
    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_get_sample_sheet = mocker.patch.object(
        APIClient,
        "get_sample_sheet",
    )
    res = runner.invoke(
        run_prefix,
        [
            str(uuid4()),
            "gncv://batch",
            "--metadata-json",
            "{bad:",
            "--email",
            "foo@bar.com",
            "--password",
            "123",
        ],
    )
    assert res.exit_code == 1
    mocked_login.assert_called_once()
    mocked_get_sample_sheet.assert_not_called()
    assert "Metadata JSON is not valid" in res.output


def test_run_prefix__not_owned_project(mocker):
    """Test run prefix failure when project is not owned."""
    runner = CliRunner()
    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_get_sample_sheet = mocker.patch.object(
        APIClient,
        "get_sample_sheet",
        side_effect=APIClientError(message="", status_code=403),
    )

    mocked_add_samples_to_project = mocker.patch.object(
        APIClient,
        "add_samples_to_project",
    )

    res = runner.invoke(
        run_prefix,
        [
            str(uuid4()),
            "gncv://batch",
            "--email",
            "foo@bar.com",
            "--password",
            "123",
        ],
    )
    assert res.exit_code == 1
    mocked_login.assert_called_once()
    mocked_get_sample_sheet.assert_called_once()
    mocked_add_samples_to_project.assert_not_called()
    assert "You do not have the sufficient permission" in res.output


def test_run_prefix__no_paths(mocker):
    """Test run prefix when no paths are present."""
    runner = CliRunner()
    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_get_sample_sheet = mocker.patch.object(
        APIClient,
        "get_sample_sheet",
        return_value=SampleSheet(**MOCKED_EMPTY_UPLOADS),
    )
    mocked_add_samples_to_project = mocker.patch.object(
        APIClient,
        "add_samples_to_project",
        return_value=UploadSamples(**{}),
    )

    res = runner.invoke(
        run_prefix,
        [
            str(uuid4()),
            "gncv://batch",
            "--email",
            "foo@bar.com",
            "--password",
            "123",
        ],
    )
    assert res.exit_code == 1
    mocked_login.assert_called_once()
    mocked_get_sample_sheet.assert_called_once()
    mocked_add_samples_to_project.assert_not_called()
    assert "No matching paths found" in res.output


def test_run_prefix__assigning_samples_no_permission(mocker):
    """Test run prefix when permission is denied for assigning samples."""
    runner = CliRunner()
    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_get_sample_sheet = mocker.patch.object(
        APIClient,
        "get_sample_sheet",
        return_value=SampleSheet(**MOCKED_UPLOADS),
    )
    mocked_add_samples_to_project = mocker.patch.object(
        APIClient,
        "add_samples_to_project",
        side_effect=APIClientError(message="", status_code=403),
    )

    res = runner.invoke(
        run_prefix,
        [
            str(uuid4()),
            "gncv://batch",
            "--email",
            "foo@bar.com",
            "--password",
            "123",
        ],
    )
    assert res.exit_code == 1
    mocked_login.assert_called_once()
    mocked_get_sample_sheet.assert_called_once()
    mocked_add_samples_to_project.assert_called_once()
    assert "You do not have the sufficient permission" in res.output


def test_run_prefix__assigning_samples_failed(mocker):
    """Test run prefix when assigning samples fails."""
    runner = CliRunner()
    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_get_sample_sheet = mocker.patch.object(
        APIClient,
        "get_sample_sheet",
        return_value=SampleSheet(**MOCKED_UPLOADS),
    )
    mocked_add_samples_to_project = mocker.patch.object(
        APIClient,
        "add_samples_to_project",
        side_effect=APIClientError(message="", status_code=404),
    )

    res = runner.invoke(
        run_prefix,
        [
            str(uuid4()),
            "gncv://batch",
            "--email",
            "foo@bar.com",
            "--password",
            "123",
        ],
    )
    assert res.exit_code == 1
    mocked_login.assert_called_once()
    mocked_get_sample_sheet.assert_called_once()
    mocked_add_samples_to_project.assert_called_once()
    assert "You do not have the sufficient permission" not in res.output
    assert "There was an error assigning" in res.output


def test_run_prefix__success_with_json(mocker):
    """Test run prefix success with optional json passed."""
    runner = CliRunner()
    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_get_sample_sheet = mocker.patch.object(
        APIClient,
        "get_sample_sheet",
        return_value=SampleSheet(**MOCKED_UPLOADS),
    )
    mocked_add_samples_to_project = mocker.patch.object(
        APIClient,
        "add_samples_to_project",
        return_value=UploadSamples(**{}),
    )

    res = runner.invoke(
        run_prefix,
        [
            str(uuid4()),
            "gncv://batch",
            "--metadata-json",
            '{"somekey": "somevalue"}',
            "--email",
            "foo@bar.com",
            "--password",
            "123",
        ],
    )
    assert res.exit_code == 0
    mocked_login.assert_called_once()
    mocked_get_sample_sheet.assert_called_once()
    mocked_add_samples_to_project.assert_called_once()
    assert "Assigning metadata to the uploaded samples." in res.output


def test_run_prefix__filter_empty(mocker):
    """Test run prefix when all paths are filtered out."""
    runner = CliRunner()
    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_get_sample_sheet = mocker.patch.object(
        APIClient,
        "get_sample_sheet",
        return_value=SampleSheet(**MOCKED_EMPTY_UPLOADS),
    )
    mocked_add_samples_to_project = mocker.patch.object(
        APIClient,
        "add_samples_to_project",
        return_value=UploadSamples(**{}),
    )

    res = runner.invoke(
        run_prefix,
        [
            str(uuid4()),
            "gncv://batch",
            "--status",
            "assigned",
            "--email",
            "foo@bar.com",
            "--password",
            "123",
        ],
    )
    assert res.exit_code == 1
    mocked_login.assert_called_once()
    mocked_get_sample_sheet.assert_called_once()
    mocked_add_samples_to_project.assert_not_called()
    assert "No matching paths found" in res.output


def test_run_prefix__filter_success(mocker):
    """Test run prefix when filter returns some paths."""
    runner = CliRunner()
    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_uploads_copy = copy.deepcopy(MOCKED_UPLOADS)
    del mocked_uploads_copy["results"][1]
    mocked_get_sample_sheet = mocker.patch.object(
        APIClient,
        "get_sample_sheet",
        return_value=SampleSheet(**mocked_uploads_copy),
    )
    mocked_add_samples_to_project = mocker.patch.object(
        APIClient,
        "add_samples_to_project",
    )

    res = runner.invoke(
        run_prefix,
        [
            str(uuid4()),
            "gncv://batch",
            "--status",
            "unassigned",
            "--email",
            "foo@bar.com",
            "--password",
            "123",
        ],
    )
    assert res.exit_code == 0
    mocked_login.assert_called_once()
    mocked_get_sample_sheet.assert_called_once()
    mocked_add_samples_to_project.assert_called_once()
    assert "Number of samples assigned to the project" in res.output
    assert "Assigning metadata to the uploaded samples." not in res.output


def test_run_prefix__success_without_last_status(mocker):
    """Test run prefix success."""
    runner = CliRunner()
    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_uploads_copy = copy.deepcopy(MOCKED_UPLOADS)
    del mocked_uploads_copy["results"][0]["fastq"]["r1"]["last_status"]
    del mocked_uploads_copy["results"][0]["fastq"]["r2"]["last_status"]
    del mocked_uploads_copy["results"][1]["fastq"]["r1"]["last_status"]
    mocked_get_sample_sheet = mocker.patch.object(
        APIClient,
        "get_sample_sheet",
        return_value=SampleSheet(**mocked_uploads_copy),
    )
    mocked_add_samples_to_project = mocker.patch.object(
        APIClient,
        "add_samples_to_project",
        return_value=UploadSamples(**{}),
    )

    res = runner.invoke(
        run_prefix,
        [
            str(uuid4()),
            "gncv://batch",
            "--email",
            "foo@bar.com",
            "--password",
            "123",
        ],
    )
    assert res.exit_code == 0
    mocked_login.assert_called_once()
    mocked_get_sample_sheet.assert_called_once()
    mocked_add_samples_to_project.assert_called_once()
    assert "Number of samples assigned to the project" in res.output
    assert "Assigning metadata to the uploaded samples." not in res.output


def test_run_prefix__success(mocker):
    """Test run prefix success."""
    runner = CliRunner()
    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_get_sample_sheet = mocker.patch.object(
        APIClient,
        "get_sample_sheet",
        return_value=SampleSheet(**MOCKED_UPLOADS),
    )
    mocked_add_samples_to_project = mocker.patch.object(
        APIClient,
        "add_samples_to_project",
        return_value=UploadSamples(**{}),
    )

    res = runner.invoke(
        run_prefix,
        [
            str(uuid4()),
            "gncv://batch",
            "--email",
            "foo@bar.com",
            "--password",
            "123",
        ],
    )
    assert res.exit_code == 0
    mocked_login.assert_called_once()
    mocked_get_sample_sheet.assert_called_once()
    mocked_add_samples_to_project.assert_called_once()
    assert "Number of samples assigned to the project" in res.output
    assert "Assigning metadata to the uploaded samples." not in res.output
