"""Test project's get merged VCF command."""

from uuid import uuid4

from click.testing import CliRunner

from gencove.client import APIClient, APIClientError
from gencove.command.projects.cli import get_merged_vcf


def test_get_merged_vcf__bad_project_id(mocker):
    """Test get merged file failure when non-uuid string is used as
    project id.
    """
    runner = CliRunner()

    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_get_project = mocker.patch.object(
        APIClient,
        "get_project",
    )

    res = runner.invoke(
        get_merged_vcf,
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
    mocked_get_project.assert_not_called()
    assert "Project ID is not valid" in res.output


def test_get_merged_vcf__not_owned_project(mocker):
    """Test get merged file failure when project is not owned."""
    mocked_response = {"detail": "Not found."}

    runner = CliRunner()

    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_get_project = mocker.patch.object(
        APIClient,
        "get_project",
        return_value=mocked_response,
        side_effect=APIClientError(message="", status_code=404),
    )

    res = runner.invoke(
        get_merged_vcf,
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
    mocked_get_project.assert_called_once()
    assert "you do not have permission required" in res.output


def test_get_merged_vcf__empty(mocker):
    """Test project doesn't have a merged VCF file."""
    project_id = str(uuid4())

    runner = CliRunner()

    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_get_project = mocker.patch.object(
        APIClient,
        "get_project",
        return_value=dict(
            id=project_id,
            name="Project Cadmus",
            description="",
            created="2020-06-11T02:14:00.541889Z",
            organization=str(uuid4()),
            webhook_url="",
            sample_count=3,
            pipeline_capabilites=str(uuid4()),
            files=[],
        ),
    )

    res = runner.invoke(
        get_merged_vcf,
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
    mocked_get_project.assert_called_once()
    assert (
        "No files to process for project {}".format(project_id) in res.output
    )


def test_get_merged_vcf_custom_filename(mocker):
    """Test project download merged VCF success with custom filename."""
    project_id = str(uuid4())
    file_id = str(uuid4())
    download_url = (
        "https://bucket.s3.amazonaws.com/output/apps/merge_vcfs/"
        "{file_id}/{file_id}.vcf.bgz".format(file_id=file_id)
    )

    runner = CliRunner()

    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_get_project = mocker.patch.object(
        APIClient,
        "get_project",
        return_value=dict(
            id=project_id,
            name="Project Cadmus",
            description="",
            created="2020-06-11T02:14:00.541889Z",
            organization=str(uuid4()),
            webhook_url="",
            sample_count=3,
            pipeline_capabilites=str(uuid4()),
            files=[
                {
                    "id": "755ec682-e4a5-414a-a5be-07e0af11cf75",
                    "s3_path": (
                        "app-data/output/apps/merge_vcfs/"
                        "{file_id}/{file_id}.vcf.bgz".format(file_id=file_id)
                    ),
                    "size": None,
                    "download_url": download_url,
                    "file_type": "impute-vcf-merged",
                }
            ],
        ),
    )

    with runner.isolated_filesystem():
        mocked_download_file = mocker.patch(
            "gencove.command.projects.get_merged_vcf.main.download.utils."
            "download_file"
        )
        res = runner.invoke(
            get_merged_vcf,
            [
                project_id,
                "--email",
                "foo@bar.com",
                "--password",
                "123",
                "--output-filename",
                "superman.vcf.gz",
            ],
        )
    assert res.exit_code == 0
    mocked_login.assert_called_once()
    mocked_get_project.assert_called_once()
    mocked_download_file.assert_called_once_with(
        "superman.vcf.gz", download_url, no_progress=False
    )


def test_get_merged_vcf__no_progress_success(mocker):
    """Test project download merged VCF success."""
    project_id = str(uuid4())
    file_id = str(uuid4())

    runner = CliRunner()

    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_get_project = mocker.patch.object(
        APIClient,
        "get_project",
        return_value=dict(
            id=project_id,
            name="Project Cadmus",
            description="",
            created="2020-06-11T02:14:00.541889Z",
            organization=str(uuid4()),
            webhook_url="",
            sample_count=3,
            pipeline_capabilites=str(uuid4()),
            files=[
                {
                    "id": "755ec682-e4a5-414a-a5be-07e0af11cf75",
                    "s3_path": (
                        "app-data/output/apps/merge_vcfs/"
                        "{file_id}/{file_id}.vcf.bgz".format(file_id=file_id)
                    ),
                    "size": None,
                    "download_url": (
                        "https://bucket.s3.amazonaws.com/output/apps/"
                        "merge_vcfs/{file_id}/{file_id}.vcf.bgz".format(
                            file_id=file_id
                        )
                    ),
                    "file_type": "impute-vcf-merged",
                }
            ],
        ),
    )

    with runner.isolated_filesystem():
        mocked_download_file = mocker.patch(
            "gencove.command.projects.get_merged_vcf.main.download.utils."
            "download_file"
        )
        res = runner.invoke(
            get_merged_vcf,
            [
                project_id,
                "--email",
                "foo@bar.com",
                "--password",
                "123",
                "--no-progress",
            ],
        )
    assert res.exit_code == 0
    mocked_login.assert_called_once()
    mocked_get_project.assert_called_once()
    mocked_download_file.assert_called_once_with(
        "{}.vcf.bgz".format(file_id),
        "https://bucket.s3.amazonaws.com/output/apps/"
        "merge_vcfs/{file_id}/{file_id}.vcf.bgz".format(file_id=file_id),
        no_progress=True,
    )


def test_get_merged_vcf__success(mocker):
    """Test project download merged VCF success."""
    project_id = str(uuid4())
    file_id = str(uuid4())

    runner = CliRunner()

    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_get_project = mocker.patch.object(
        APIClient,
        "get_project",
        return_value=dict(
            id=project_id,
            name="Project Cadmus",
            description="",
            created="2020-06-11T02:14:00.541889Z",
            organization=str(uuid4()),
            webhook_url="",
            sample_count=3,
            pipeline_capabilites=str(uuid4()),
            files=[
                {
                    "id": "755ec682-e4a5-414a-a5be-07e0af11cf75",
                    "s3_path": (
                        "app-data/output/apps/merge_vcfs/"
                        "{file_id}/{file_id}.vcf.bgz".format(file_id=file_id)
                    ),
                    "size": None,
                    "download_url": (
                        "https://bucket.s3.amazonaws.com/output/apps/"
                        "merge_vcfs/{file_id}/{file_id}.vcf.bgz".format(
                            file_id=file_id
                        )
                    ),
                    "file_type": "impute-vcf-merged",
                }
            ],
        ),
    )

    with runner.isolated_filesystem():
        mocked_download_file = mocker.patch(
            "gencove.command.projects.get_merged_vcf.main.download.utils."
            "download_file"
        )
        res = runner.invoke(
            get_merged_vcf,
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
    mocked_get_project.assert_called_once()
    mocked_download_file.assert_called_once_with(
        "{}.vcf.bgz".format(file_id),
        "https://bucket.s3.amazonaws.com/output/apps/"
        "merge_vcfs/{file_id}/{file_id}.vcf.bgz".format(file_id=file_id),
        no_progress=False,
    )
