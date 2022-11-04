"""Test project's get merged VCF command."""

from uuid import uuid4

from click.testing import CliRunner

from gencove.client import APIClient, APIClientError, APIClientTimeout
from gencove.command.projects.cli import get_merged_vcf
from gencove.models import Project


def test_get_merged_vcf__bad_project_id(mocker):
    """Test get merged file failure when non-uuid string is used as
    project id.
    """
    runner = CliRunner()

    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_get_project = mocker.patch.object(
        APIClient,
        "get_project",
        return_value=Project(id=str(uuid4())),
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
        side_effect=APIClientError(message="", status_code=403),
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
    assert "You do not have the sufficient permission" in res.output


def test_get_merged_vcf__empty(mocker):
    """Test project doesn't have a merged VCF file."""
    project_id = str(uuid4())

    runner = CliRunner()

    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_get_project = mocker.patch.object(
        APIClient,
        "get_project",
        return_value=Project(
            id=project_id,
            name="Project Cadmus",
            description="",
            created="2020-06-11T02:14:00.541889Z",
            organization=str(uuid4()),
            sample_count=3,
            pipeline_capabilities=str(uuid4()),
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
    assert f"No files to process for project {project_id}" in res.output


def test_get_merged_vcf_custom_filename(mocker):
    """Test project download merged VCF success with custom filename."""
    project_id = str(uuid4())
    file_id = str(uuid4())
    download_url = (
        "https://bucket.s3.amazonaws.com/output/apps/merge_vcfs/"
        f"{file_id}/{file_id}.vcf.bgz"
    )

    runner = CliRunner()

    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_get_project = mocker.patch.object(
        APIClient,
        "get_project",
        return_value=Project(
            id=project_id,
            name="Project Cadmus",
            description="",
            created="2020-06-11T02:14:00.541889Z",
            organization=str(uuid4()),
            sample_count=3,
            pipeline_capabilities=str(uuid4()),
            files=[
                {
                    "id": "755ec682-e4a5-414a-a5be-07e0af11cf75",
                    "s3_path": (
                        "app-data/output/apps/merge_vcfs/"
                        f"{file_id}/{file_id}.vcf.bgz"
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
        return_value=Project(
            id=project_id,
            name="Project Cadmus",
            description="",
            created="2020-06-11T02:14:00.541889Z",
            organization=str(uuid4()),
            sample_count=3,
            pipeline_capabilities=str(uuid4()),
            files=[
                {
                    "id": "755ec682-e4a5-414a-a5be-07e0af11cf75",
                    "s3_path": (
                        "app-data/output/apps/merge_vcfs/"
                        f"{file_id}/{file_id}.vcf.bgz"
                    ),
                    "size": None,
                    "download_url": (
                        "https://bucket.s3.amazonaws.com/output/apps/"
                        f"merge_vcfs/{file_id}/{file_id}.vcf.bgz"
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
        f"{file_id}.vcf.bgz",
        "https://bucket.s3.amazonaws.com/output/apps/"
        f"merge_vcfs/{file_id}/{file_id}.vcf.bgz",
        no_progress=True,
    )


def test_get_merged_vcf__slow_response_retry(mocker):
    """Test project download merged VCF slow response retry."""
    project_id = str(uuid4())

    runner = CliRunner()

    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_get_project = mocker.patch.object(
        APIClient,
        "get_project",
        side_effect=APIClientTimeout("Could not connect to the api server"),
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
    assert res.exit_code == 1
    mocked_login.assert_called_once()
    assert mocked_get_project.call_count == 5
    mocked_download_file.assert_not_called()


def test_get_merged_vcf__success(mocker):
    """Test project download merged VCF success."""
    project_id = str(uuid4())
    file_id = str(uuid4())

    runner = CliRunner()

    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_get_project = mocker.patch.object(
        APIClient,
        "get_project",
        return_value=Project(
            id=project_id,
            name="Project Cadmus",
            description="",
            created="2020-06-11T02:14:00.541889Z",
            organization=str(uuid4()),
            sample_count=3,
            pipeline_capabilities=str(uuid4()),
            files=[
                {
                    "id": "755ec682-e4a5-414a-a5be-07e0af11cf75",
                    "s3_path": (
                        "app-data/output/apps/merge_vcfs/"
                        f"{file_id}/{file_id}.vcf.bgz"
                    ),
                    "size": None,
                    "download_url": (
                        "https://bucket.s3.amazonaws.com/output/apps/"
                        f"merge_vcfs/{file_id}/{file_id}.vcf.bgz"
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
        f"{file_id}.vcf.bgz",
        "https://bucket.s3.amazonaws.com/output/apps/"
        f"merge_vcfs/{file_id}/{file_id}.vcf.bgz",
        no_progress=False,
    )


def test_get_merged_vcf__success__project_with_legacy_webhhok_url(mocker):
    """Test project download merged VCF success."""
    project_id = str(uuid4())
    file_id = str(uuid4())

    runner = CliRunner()

    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_get_project = mocker.patch.object(
        APIClient,
        "get_project",
        return_value=Project(
            id=project_id,
            name="Project Cadmus",
            description="",
            created="2020-06-11T02:14:00.541889Z",
            organization=str(uuid4()),
            webhook_url="",
            sample_count=3,
            pipeline_capabilities=str(uuid4()),
            files=[
                {
                    "id": "755ec682-e4a5-414a-a5be-07e0af11cf75",
                    "s3_path": (
                        "app-data/output/apps/merge_vcfs/"
                        f"{file_id}/{file_id}.vcf.bgz"
                    ),
                    "size": None,
                    "download_url": (
                        "https://bucket.s3.amazonaws.com/output/apps/"
                        f"merge_vcfs/{file_id}/{file_id}.vcf.bgz"
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
        f"{file_id}.vcf.bgz",
        "https://bucket.s3.amazonaws.com/output/apps/"
        f"merge_vcfs/{file_id}/{file_id}.vcf.bgz",
        no_progress=False,
    )
