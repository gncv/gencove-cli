"""Test project's get jointcalled VCF command."""

from uuid import uuid4

from click.testing import CliRunner

from gencove.client import APIClient, APIClientError, APIClientTimeout
from gencove.command.projects.cli import get_jointcalled_vcf
from gencove.models import Project

from pydantic import HttpUrl  # pylint: disable=wrong-import-order


def test_get_jointcalled_vcf__bad_project_id(mocker):
    """Test jointcalled vcf with wrong project id"""
    runner = CliRunner()

    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_get_project = mocker.patch.object(
        APIClient,
        "get_project",
        return_value=Project(id=str(uuid4())),
    )

    res = runner.invoke(
        get_jointcalled_vcf,
        [
            "1111111",
            "--email",
            "foo@bar.com",
            "--password",
            "123",
        ],
    )

    assert res.exit_code == 1
    mocked_login.assert_not_called()
    mocked_get_project.assert_not_called()
    assert "Project ID is not valid" in res.output


def test_get_jointcalled_vcf__not_owned_project(mocker):
    """Test jointcalled vcf with not owned project"""
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
        get_jointcalled_vcf,
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


def test_get_jointcalled_vcf__empty(mocker):
    """Test jointcalled vcf with empty project shows error message"""
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

    with runner.isolated_filesystem():
        mocked_download_file = mocker.patch(
            "gencove.command.projects.get_jointcalled_vcf.main.download.utils."
            "download_file"
        )
        res = runner.invoke(
            get_jointcalled_vcf,
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
    mocked_download_file.assert_not_called()
    assert f"Project {project_id} has no jointcalled VCF files." in res.output


def test_get_jointcalled_vcf_custom_output_folder(mocker):
    """Test jointcalled vcf with custom output folder"""
    project_id = str(uuid4())
    file_id = str(uuid4())
    download_url = HttpUrl(
        "https://bucket.s3.amazonaws.com/jointcalled_vcfs/"
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
                    "s3_path": ("jointcalled_vcfs/" f"{file_id}/{file_id}.vcf.bgz"),
                    "size": None,
                    "download_url": download_url,
                    "file_type": "jointcalled-vcf",
                }
            ],
        ),
    )

    with runner.isolated_filesystem():
        mocked_download_file = mocker.patch(
            "gencove.command.projects.get_jointcalled_vcf.main.download.utils."
            "download_file"
        )
        res = runner.invoke(
            get_jointcalled_vcf,
            [
                project_id,
                "--email",
                "foo@bar.com",
                "--password",
                "123",
                "--output-folder",
                "custom_folder",
            ],
        )
    assert res.exit_code == 0
    mocked_login.assert_called_once()
    mocked_get_project.assert_called_once()
    mocked_download_file.assert_called_once_with(
        f"custom_folder/{file_id}.vcf.bgz", download_url, no_progress=False
    )


def test_get_jointcalled_vcf__no_progress_success(mocker):
    """Test jointcalled vcf with no progress"""
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
                    "s3_path": ("jointcalled_vcfs/" f"{file_id}/{file_id}.vcf.bgz"),
                    "size": None,
                    "download_url": (
                        "https://bucket.s3.amazonaws.com/"
                        f"jointcalled_vcfs/{file_id}/{file_id}.vcf.bgz"
                    ),
                    "file_type": "jointcalled-vcf",
                }
            ],
        ),
    )

    with runner.isolated_filesystem():
        mocked_download_file = mocker.patch(
            "gencove.command.projects.get_jointcalled_vcf.main.download.utils."
            "download_file"
        )
        res = runner.invoke(
            get_jointcalled_vcf,
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
        f"./{file_id}.vcf.bgz",
        HttpUrl(
            "https://bucket.s3.amazonaws.com/"
            f"jointcalled_vcfs/{file_id}/{file_id}.vcf.bgz"
        ),
        no_progress=True,
    )


def test_get_jointcalled_vcf__slow_response_retry(mocker):
    """Test jointcalled vcf with slow response retry"""
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
            "gencove.command.projects.get_jointcalled_vcf.main.download.utils."
            "download_file"
        )
        res = runner.invoke(
            get_jointcalled_vcf,
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


def test_get_jointcalled_vcf__success(mocker):
    """Test jointcalled vcf with success"""
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
                        "app-data/output/apps/jointcalled_vcfs/"
                        f"{file_id}/{file_id}.vcf.bgz"
                    ),
                    "size": None,
                    "download_url": (
                        "https://bucket.s3.amazonaws.com/output/apps/"
                        f"jointcalled_vcfs/{file_id}/{file_id}.vcf.bgz"
                    ),
                    "file_type": "jointcalled-vcf",
                }
            ],
        ),
    )

    with runner.isolated_filesystem():
        mocked_download_file = mocker.patch(
            "gencove.command.projects.get_jointcalled_vcf.main.download.utils."
            "download_file"
        )
        res = runner.invoke(
            get_jointcalled_vcf,
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
        f"./{file_id}.vcf.bgz",
        HttpUrl(
            "https://bucket.s3.amazonaws.com/output/apps/"
            f"jointcalled_vcfs/{file_id}/{file_id}.vcf.bgz"
        ),
        no_progress=False,
    )


def test_get_jointcalled_vcf__multiple_files(mocker):
    """Test jointcalled vcf with multiple files"""
    project_id = str(uuid4())
    file_id1 = str(uuid4())
    file_id2 = str(uuid4())

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
                        "app-data/output/apps/jointcalled_vcfs/"
                        f"{file_id1}/{file_id1}.vcf.bgz"
                    ),
                    "size": None,
                    "download_url": (
                        "https://bucket.s3.amazonaws.com/output/apps/"
                        f"jointcalled_vcfs/{file_id1}/{file_id1}.vcf.bgz"
                    ),
                    "file_type": "jointcalled-vcf",
                },
                {
                    "id": "866fd793-f5b6-525b-b6cf-18f1b35e28e6",
                    "s3_path": (
                        "app-data/output/apps/jointcalled_vcfs/"
                        f"{file_id2}/{file_id2}.vcf.bgz"
                    ),
                    "size": None,
                    "download_url": (
                        "https://bucket.s3.amazonaws.com/output/apps/"
                        f"jointcalled_vcfs/{file_id2}/{file_id2}.vcf.bgz"
                    ),
                    "file_type": "jointcalled-vcf_indexed",
                },
            ],
        ),
    )

    with runner.isolated_filesystem():
        mocked_download_file = mocker.patch(
            "gencove.command.projects.get_jointcalled_vcf.main.download.utils."
            "download_file"
        )
        res = runner.invoke(
            get_jointcalled_vcf,
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
    assert mocked_download_file.call_count == 2
    mocked_download_file.assert_any_call(
        f"./{file_id1}.vcf.bgz",
        HttpUrl(
            "https://bucket.s3.amazonaws.com/output/apps/"
            f"jointcalled_vcfs/{file_id1}/{file_id1}.vcf.bgz"
        ),
        no_progress=False,
    )
    mocked_download_file.assert_any_call(
        f"./{file_id2}.vcf.bgz",
        HttpUrl(
            "https://bucket.s3.amazonaws.com/output/apps/"
            f"jointcalled_vcfs/{file_id2}/{file_id2}.vcf.bgz"
        ),
        no_progress=False,
    )


def test_get_jointcalled_vcf__mixed_file_types(mocker):
    """Test jointcalled vcf with mixed file types"""
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
                        "app-data/output/apps/jointcalled_vcfs/"
                        f"{file_id}/{file_id}.vcf.bgz"
                    ),
                    "size": None,
                    "download_url": (
                        "https://bucket.s3.amazonaws.com/output/apps/"
                        f"jointcalled_vcfs/{file_id}/{file_id}.vcf.bgz"
                    ),
                    "file_type": "jointcalled-vcf",
                },
                {
                    "id": "866fd793-f5b6-525b-b6cf-18f1b35e28e6",
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
                },
            ],
        ),
    )

    with runner.isolated_filesystem():
        mocked_download_file = mocker.patch(
            "gencove.command.projects.get_jointcalled_vcf.main.download.utils."
            "download_file"
        )
        res = runner.invoke(
            get_jointcalled_vcf,
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
        f"./{file_id}.vcf.bgz",
        HttpUrl(
            "https://bucket.s3.amazonaws.com/output/apps/"
            f"jointcalled_vcfs/{file_id}/{file_id}.vcf.bgz"
        ),
        no_progress=False,
    )
