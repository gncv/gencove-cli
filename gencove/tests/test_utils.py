"""Tests for utils of Gencove CLI."""
import csv
import os

from click.testing import CliRunner

from gencove.command.download.utils import (
    _get_prefix_parts,
    get_download_template_format_params,
)
from gencove.command.upload.utils import upload_file, parse_fastqs_map_file
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
    """Test proper processing of parts in download template."""
    client_id = "12345"
    gencove_id = "1"
    template = DOWNLOAD_TEMPLATE.format(
        **get_download_template_format_params(client_id, gencove_id)
    )

    resp = _get_prefix_parts(template)

    assert resp.dirs == "{}/{}".format(client_id, gencove_id)
    assert resp.filename == "{}_{{{}}}".format(
        gencove_id, DownloadTemplateParts.file_type
    )
    assert resp.file_extension == "{{{}}}".format(
        DownloadTemplateParts.file_extension
    )

    template2 = "{client_id}-{gencove_id}_{file_type}".format(
        **get_download_template_format_params(client_id, gencove_id)
    )
    resp = _get_prefix_parts(template2)
    assert resp.dirs == ""
    assert resp.filename == "{}-{}_{{{}}}".format(
        client_id, gencove_id, DownloadTemplateParts.file_type
    )
    assert resp.file_extension == ""

    template3 = "{client_id}-{gencove_id}_{file_type}.vcf.gz".format(
        **get_download_template_format_params(client_id, gencove_id)
    )
    resp = _get_prefix_parts(template3)
    assert resp.dirs == ""
    assert resp.filename == "{}-{}_{{{}}}".format(
        client_id, gencove_id, DownloadTemplateParts.file_type
    )
    assert resp.file_extension == "vcf.gz"


def test_parse_fastqs_map_file():
    runner = CliRunner()
    with runner.isolated_filesystem():
        os.mkdir("test_dir")
        with open("test_dir/test.fastq.gz", "w") as fastq_file1:
            fastq_file1.write("AAABBB")

        with open("test_dir/test_2.fastq.gz", "w") as fastq_file2:
            fastq_file2.write("AAABBB")

        with open("test_dir/test_3.fastq.gz", "w") as fastq_file3:
            fastq_file3.write("AAABBB")

        with open("test_map.csv", "w") as map_file:
            writer = csv.writer(map_file)
            writer.writerows(
                [
                    ["batch", "client_id", "r1_notation", "path"],
                    ["foob", "barid", "r1", "test_dir/test.fastq.gz"],
                    ["foob", "barid", "r2", "test_dir/test_2.fastq.gz"],
                    ["foob", "barid", "r1", "test_dir/test_3.fastq.gz"],
                ]
            )

        fastqs = parse_fastqs_map_file("test_map.csv")
        assert len(fastqs) == 2
        assert ("foob", "barid", "r1") in fastqs
        assert ("foob", "barid", "r2") in fastqs
        assert len(fastqs[("foob", "barid", "r1")]) == 2
        assert fastqs[("foob", "barid", "r1")][0] == "test_dir/test.fastq.gz"
        assert (
            fastqs[("foob", "barid", "r1")][1] == "test_dir/test_3.fastq.gz"
        )
