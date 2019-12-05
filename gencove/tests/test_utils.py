"""Tests for utils of Gencove CLI."""
from click.testing import CliRunner

from gencove.command.upload.utils import upload_file
from gencove.command.download.utils import _get_filename_dirs_prefix
from gencove.constants import DOWNLOAD_TEMPLATE, DownloadTemplateParts


def test_upload_file(mocker):
    """Sanity check upload function."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("foo.txt", "w") as fastq_file:
            fastq_file.write("AAABBB")
        mocked_s3_client = mocker.Mock()
        assert upload_file(
            mocked_s3_client,
            "foo.txt",
            "foo-bucket",
            object_name="foo-object.txt",
        )
        mocked_s3_client.upload_file.assert_called_once()


def test___get_filename_dirs_prefix():
    client_id = "12345"
    gencove_id = "1"
    template = DOWNLOAD_TEMPLATE.format(
        **{
            DownloadTemplateParts.client_id: client_id,
            DownloadTemplateParts.gencove_id: gencove_id,
            DownloadTemplateParts.file_type: "{{{}}}".format(
                DownloadTemplateParts.file_type
            ),
            DownloadTemplateParts.file_extension: "{{{}}}".format(
                DownloadTemplateParts.file_extension
            ),
        }
    )

    resp = _get_filename_dirs_prefix(template)

    assert resp.dirs == "{}/{}".format(client_id, gencove_id)
    assert resp.filename == "{}_{{{}}}".format(
        gencove_id, DownloadTemplateParts.file_type
    )
    assert resp.file_extension == "{{{}}}".format(
        DownloadTemplateParts.file_extension
    )
