"""Test project's batches list command."""

from uuid import uuid4

from click.testing import CliRunner

from gencove.client import APIClient, APIClientTimeout  # noqa: I100
from gencove.command.projects.cli import get_batch


def test_get_batch__empty(mocker):
    """Test project has not batches."""
    runner = CliRunner()
    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    batch_id = str(uuid4())
    mocked_get_batch = mocker.patch.object(
        APIClient,
        "get_batch",
        return_value=dict(
            id=batch_id,
            name="cli-test-1",
            batch_type="batch-type-1",
            sample_ids=["sample-id-1", "sample-id-2"],
            last_status=dict(
                id="last-status-id-1",
                status="running",
                created="2020-08-02T22:13:54.547167Z",
            ),
            files=[],
        ),
    )

    res = runner.invoke(
        get_batch, [batch_id, "--email", "foo@bar.com", "--password", "123"]
    )
    assert res.exit_code == 1
    mocked_login.assert_called_once()
    mocked_get_batch.assert_called_once()
    assert (
        res.output == "ERROR: There are no deliverables available for batch"
        " {}.\nAborted!\n".format(batch_id)
    )


def test_get_batch__not_empty(mocker):
    """Test project batches being outputed to the shell."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        mocked_login = mocker.patch.object(
            APIClient, "login", return_value=None
        )
        batch_id = str(uuid4())
        mocked_get_batch = mocker.patch.object(
            APIClient,
            "get_batch",
            return_value=dict(
                id=batch_id,
                name="cli-test-1",
                batch_type="batch-type-1",
                sample_ids=["sample-id-1", "sample-id-2"],
                last_status=dict(
                    id="last-status-id-1",
                    status="running",
                    created="2020-08-02T22:13:54.547167Z",
                ),
                files=[
                    dict(
                        id="file-id-1",
                        s3_path=(
                            "output/simple_vcf2finalreport/job-id-1/"
                            "simple_vcf2finalreport/report.zip"
                        ),
                        size=None,
                        download_url=(
                            "https://bucket.s3.amazonaws.com/output/"
                            "simple_vcf2finalreport/job-id-1/"
                            "simple_vcf2finalreport/report.zip"
                        ),
                        file_type="report-zip",
                    )
                ],
            ),
        )
        mocked_download_file = mocker.patch(
            "gencove.command.projects.get_batch.main.download.utils."
            "download_file"
        )
        res = runner.invoke(
            get_batch,
            [
                batch_id,
                "--email",
                "foo@bar.com",
                "--password",
                "123",
                "--output-filename",
                "test.zip",
            ],
        )
    assert res.exit_code == 0
    mocked_login.assert_called_once()
    mocked_get_batch.assert_called_once()
    mocked_download_file.assert_called_once_with(
        "test.zip",
        "https://bucket.s3.amazonaws.com/output/simple_vcf2finalreport/"
        "job-id-1/simple_vcf2finalreport/report.zip",
        no_progress=False,
    )


def test_get_batch__no_progress_not_empty(mocker):
    """Test project batches being outputed to the shell without progress."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        mocked_login = mocker.patch.object(
            APIClient, "login", return_value=None
        )
        batch_id = str(uuid4())
        mocked_get_batch = mocker.patch.object(
            APIClient,
            "get_batch",
            return_value=dict(
                id=batch_id,
                name="cli-test-1",
                batch_type="batch-type-1",
                sample_ids=["sample-id-1", "sample-id-2"],
                last_status=dict(
                    id="last-status-id-1",
                    status="running",
                    created="2020-08-02T22:13:54.547167Z",
                ),
                files=[
                    dict(
                        id="file-id-1",
                        s3_path=(
                            "output/simple_vcf2finalreport/job-id-1/"
                            "simple_vcf2finalreport/report.zip"
                        ),
                        size=None,
                        download_url=(
                            "https://bucket.s3.amazonaws.com/output/"
                            "simple_vcf2finalreport/job-id-1/"
                            "simple_vcf2finalreport/report.zip"
                        ),
                        file_type="report-zip",
                    )
                ],
            ),
        )
        mocked_download_file = mocker.patch(
            "gencove.command.projects.get_batch.main.download.utils."
            "download_file"
        )
        res = runner.invoke(
            get_batch,
            [
                batch_id,
                "--email",
                "foo@bar.com",
                "--password",
                "123",
                "--output-filename",
                "test.zip",
                "--no-progress",
            ],
        )
    assert res.exit_code == 0
    mocked_login.assert_called_once()
    mocked_get_batch.assert_called_once()
    mocked_download_file.assert_called_once_with(
        "test.zip",
        "https://bucket.s3.amazonaws.com/output/simple_vcf2finalreport/"
        "job-id-1/simple_vcf2finalreport/report.zip",
        no_progress=True,
    )


def test_get_batch__not_empty__slow_response_retry(mocker):
    """Test project batches slow response retry."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        mocked_login = mocker.patch.object(
            APIClient, "login", return_value=None
        )
        batch_id = str(uuid4())
        mocked_get_batch = mocker.patch.object(
            APIClient,
            "get_batch",
            side_effect=APIClientTimeout(
                "Could not connect to the api server"
            ),
        )
        mocked_download_file = mocker.patch(
            "gencove.command.projects.get_batch.main.download.utils."
            "download_file"
        )
        res = runner.invoke(
            get_batch,
            [
                batch_id,
                "--email",
                "foo@bar.com",
                "--password",
                "123",
                "--output-filename",
                "test.zip",
            ],
        )
    assert res.exit_code == 1
    mocked_login.assert_called_once()
    assert mocked_get_batch.call_count == 2
    mocked_download_file.assert_not_called()
