"""Tests for utils of Gencove CLI."""
from click.testing import CliRunner

from gencove.command.download.utils import _get_filename_dirs_prefix
from gencove.command.upload.utils import upload_file
from gencove.constants import DOWNLOAD_TEMPLATE, DownloadTemplateParts
from gencove.utils import get_download_template_format_params


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
    """Test proper processing of parts in download template."""
    client_id = "12345"
    gencove_id = "1"
    template = DOWNLOAD_TEMPLATE.format(
        **get_download_template_format_params(client_id, gencove_id)
    )

    resp = _get_filename_dirs_prefix(template)

    assert resp.dirs == "{}/{}".format(client_id, gencove_id)
    assert resp.filename == "{}_{{{}}}".format(
        gencove_id, DownloadTemplateParts.file_type
    )
    assert resp.file_extension == "{{{}}}".format(
        DownloadTemplateParts.file_extension
    )
