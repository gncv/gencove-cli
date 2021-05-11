"""Test download command."""
from uuid import uuid4

from click.testing import CliRunner

from gencove.client import APIClient
from gencove.command.samples.cli import download_file

import requests  # pylint: disable=wrong-import-order


class BasicRequestMock:
    """Basic mock for request object"""

    def __init__(self, headers, content):
        self.headers = dict(headers, **{"content-length": len(content)})
        self.content = content

    def iter_content(self, **kwargs):
        """Return iterable of content"""
        chunk_size = kwargs["chunk_size"] if "chunk_size" in kwargs else 0
        if chunk_size <= 0:
            chunk_size = len(self.content)
        if chunk_size >= len(self.content):
            return [self.content]
        chunk_count = len(self.content) / chunk_size
        if len(self.content) % chunk_size != 0:
            chunk_count += 1
        return (
            self.content[
                (i * chunk_size) : min(  # noqa: E203
                    (i + 1) * chunk_size, len(self.content)
                )
            ]
            for i in range(chunk_count)
        )

    def raise_for_status(self):
        """Not implemented"""

    def __enter__(self):
        return self

    def __exit__(self, value_type, value, trace):
        """Not implemented"""


def test_samples_download_file_local(mocker):
    """Test command outputs to local destination."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        mocked_login = mocker.patch.object(
            APIClient, "login", return_value=None
        )
        sample_id = str(uuid4())
        file_type = "txt"
        last_status_id = str(uuid4())
        archive_last_status_id = str(uuid4())
        file_id = str(uuid4())
        file_content = bytes(b"\0" * 1024)
        file_path = "bar.txt"
        response_headers = dict()
        mocked_sample_details = mocker.patch.object(
            APIClient,
            "get_sample_details",
            return_value={
                "id": sample_id,
                "client_id": 1,
                "last_status": {
                    "id": last_status_id,
                    "status": "succeeded",
                    "created": "2020-07-28T12:46:22.719862Z",
                },
                "archive_last_status": {
                    "id": archive_last_status_id,
                    "status": "available",
                    "created": "2020-07-28T12:46:22.719862Z",
                    "transition_cutoff": "2020-08-28T12:46:22.719862Z",
                },
                "files": [
                    {
                        "id": file_id,
                        "file_type": file_type,
                        "download_url": "https://foo.com/bar.txt",
                    }
                ],
            },
        )
        mocked_request = mocker.patch.object(
            requests,
            "get",
            return_value=BasicRequestMock(response_headers, file_content),
        )
        res = runner.invoke(
            download_file,
            [
                sample_id,
                file_type,
                file_path,
                "--email",
                "foo@bar.com",
                "--password",
                "12345",
            ],
        )
        assert res.exit_code == 0
        mocked_login.assert_called_once()
        mocked_sample_details.assert_called_once()
        mocked_request.assert_called_once()
        with open(file_path, "rb") as local_file:
            assert file_content == local_file.read()


def test_samples_download_file_stdout(mocker):
    """Test command outputs to stdout."""
    runner = CliRunner()
    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    sample_id = str(uuid4())
    file_type = "txt"
    last_status_id = str(uuid4())
    archive_last_status_id = str(uuid4())
    file_id = str(uuid4())
    file_content = bytes(b"\0" * 1024)
    response_headers = dict()
    mocked_sample_details = mocker.patch.object(
        APIClient,
        "get_sample_details",
        return_value={
            "id": sample_id,
            "client_id": 1,
            "last_status": {
                "id": last_status_id,
                "status": "succeeded",
                "created": "2020-07-28T12:46:22.719862Z",
            },
            "archive_last_status": {
                "id": archive_last_status_id,
                "status": "available",
                "created": "2020-07-28T12:46:22.719862Z",
                "transition_cutoff": "2020-08-28T12:46:22.719862Z",
            },
            "files": [
                {
                    "id": file_id,
                    "file_type": file_type,
                    "download_url": "https://foo.com/bar.txt",
                }
            ],
        },
    )
    mocked_request = mocker.patch.object(
        requests,
        "get",
        return_value=BasicRequestMock(response_headers, file_content),
    )
    res = runner.invoke(
        download_file,
        [
            sample_id,
            file_type,
            "-",
            "--email",
            "foo@bar.com",
            "--password",
            "12345",
        ],
    )
    assert res.exit_code == 0
    mocked_login.assert_called_once()
    mocked_sample_details.assert_called_once()
    mocked_request.assert_called_once()
    assert file_content == res.output.encode()


def test_samples_download_file_directory():
    """Test command fails when writing to directory."""
    runner = CliRunner()
    with runner.isolated_filesystem():
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
        assert "ERROR" in res.output
