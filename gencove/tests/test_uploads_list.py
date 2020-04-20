"""Test uploads list command."""
# pylint: disable=wrong-import-order
import io
import sys
from uuid import uuid4

from click import echo
from click.testing import CliRunner

from gencove.client import APIClient  # noqa: I100
from gencove.command.uploads.list.cli import list_uploads


def test_list_empty(mocker):
    """Test user has no uploads."""
    runner = CliRunner()
    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_get_projects = mocker.patch.object(
        APIClient,
        "get_sample_sheet",
        return_value=dict(results=[], meta=dict(next=None)),
    )
    res = runner.invoke(
        list_uploads, ["--email", "foo@bar.com", "--password", "123"]
    )
    assert res.exit_code == 0
    mocked_login.assert_called_once()
    mocked_get_projects.assert_called_once()
    assert "" in res.output


MOCKED_UPLOADS = dict(
    meta=dict(next=None),
    results=[
        {
            "client_id": "clientid1",
            "fastq": {
                "r1": {
                    "upload": str(uuid4()),
                    "destination_path": "gncv://batch1/clientid1_R1.fastq.gz",
                },
                "r2": {
                    "upload": str(uuid4()),
                    "destination_path": "gncv://batch1/clientid1_R@.fastq.gz",
                },
            },
        },
        {
            "client_id": "clientid2",
            "fastq": {
                "r1": {
                    "upload": str(uuid4()),
                    "destination_path": "gncv://batch2/clientid2_R1.fastq.gz",
                }
            },
        },
    ],
)


def test_list_uploads(mocker):
    """Test list uploads being outputed to the shell."""
    runner = CliRunner()
    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_get_sample_sheet = mocker.patch.object(
        APIClient, "get_sample_sheet", return_value=MOCKED_UPLOADS
    )
    res = runner.invoke(
        list_uploads, ["--email", "foo@bar.com", "--password", "123"]
    )
    print(res.output)
    assert res.exit_code == 0
    mocked_login.assert_called_once()
    mocked_get_sample_sheet.assert_called_once()

    output_line = io.BytesIO()
    sys.stdout = output_line
    echo(
        "\t".join(
            [
                MOCKED_UPLOADS["results"][0]["client_id"],
                MOCKED_UPLOADS["results"][0]["fastq"]["r1"]["upload"],
                MOCKED_UPLOADS["results"][0]["fastq"]["r1"][
                    "destination_path"
                ],
                MOCKED_UPLOADS["results"][0]["fastq"]["r2"]["upload"],
                MOCKED_UPLOADS["results"][0]["fastq"]["r2"][
                    "destination_path"
                ],
            ]
        )
    )
    echo(
        "\t".join(
            [
                MOCKED_UPLOADS["results"][1]["client_id"],
                MOCKED_UPLOADS["results"][1]["fastq"]["r1"]["upload"],
                MOCKED_UPLOADS["results"][1]["fastq"]["r1"][
                    "destination_path"
                ],
            ]
        )
    )
    assert output_line.getvalue() == res.output.encode()
