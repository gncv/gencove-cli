"""Tests for utils of Gencove CLI."""
import csv
import os

from click.testing import CliRunner

from gencove.command.download.utils import (
    _get_prefix_parts,
    build_file_path,
    get_download_template_format_params,
)
from gencove.command.upload.utils import (
    _validate_header,
    parse_fastqs_map_file,
    upload_file,
)
from gencove.command.utils import is_valid_uuid
from gencove.constants import DOWNLOAD_TEMPLATE, DownloadTemplateParts
from gencove.exceptions import ValidationError


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


def test_download_template_tokens():
    """Ensure download tokens are only the ones defined."""
    assert [
        "client_id",
        "gencove_id",
        "file_type",
        "file_extension",
        "default_filename",
    ] == list(DownloadTemplateParts._asdict().values())


# pylint: disable=too-many-locals
def test_build_file_path():
    """Test token combinations when building a file path."""
    client_id = "12345"
    gencove_id = "1"
    deliverable = {
        "download_url": "https://example.com/file.txt",
        "file_type": "txt",
    }
    # file with prefix will never have client_id and gencove_id. 0 is default
    file_with_prefix0 = "{client_id}/{gencove_id}/{default_filename}".format(
        **get_download_template_format_params(client_id, gencove_id)
    )
    file_with_prefix1 = "{client_id}".format(
        **get_download_template_format_params(client_id, gencove_id)
    )
    file_with_prefix2 = "{gencove_id}".format(
        **get_download_template_format_params(client_id, gencove_id)
    )
    file_with_prefix3 = "{file_type}"
    file_with_prefix4 = "{file_extension}"
    file_with_prefix5 = "{default_filename}"
    file_with_prefix6 = "{default_filename}.{file_extension}"
    file_with_prefix7 = "{default_filename}.{client_id}".format(
        **get_download_template_format_params(client_id, gencove_id)
    )
    file_with_prefix8 = "{client_id}.{default_filename}".format(
        **get_download_template_format_params(client_id, gencove_id)
    )
    file_with_prefix9 = "{file_extension}_{client_id}".format(
        **get_download_template_format_params(client_id, gencove_id)
    )
    download_to = "."
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = build_file_path(deliverable, file_with_prefix0, download_to)
        # default_filename is always a full filename with any extensions
        assert result == "./{}/{}/{}".format(
            client_id, gencove_id, "file.txt"
        )
        result = build_file_path(deliverable, file_with_prefix1, download_to)
        assert result == "./{}".format(client_id)
        result = build_file_path(deliverable, file_with_prefix2, download_to)
        assert result == "./{}".format(gencove_id)
        result = build_file_path(deliverable, file_with_prefix3, download_to)
        assert result == "./{}".format("txt")
        result = build_file_path(deliverable, file_with_prefix4, download_to)
        assert result == "./{}".format("txt")
        result = build_file_path(deliverable, file_with_prefix5, download_to)
        assert result == "./{}".format("file.txt")
        result = build_file_path(deliverable, file_with_prefix6, download_to)
        assert result == "./{}.{}".format("file.txt", "txt")
        result = build_file_path(deliverable, file_with_prefix7, download_to)
        assert result == "./{}.{}".format("file.txt", client_id)
        result = build_file_path(deliverable, file_with_prefix8, download_to)
        assert result == "./{}.{}".format(client_id, "file.txt")
        result = build_file_path(deliverable, file_with_prefix9, download_to)
        assert result == "./{}_{}".format("txt", client_id)


def test___get_filename_dirs_prefix():
    """Test proper processing of parts in download template."""
    client_id = "12345"
    gencove_id = "1"
    template = DOWNLOAD_TEMPLATE.format(
        **get_download_template_format_params(client_id, gencove_id)
    )

    resp = _get_prefix_parts(template)

    assert resp.dirs == "{}/{}".format(client_id, gencove_id)
    assert resp.filename == "{{{}}}".format(
        DownloadTemplateParts.default_filename
    )
    assert resp.file_extension == ""

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
    """Test parsing of map file into dict."""
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
                    ["client_id", "r_notation", "path"],
                    ["barid", "r1", "test_dir/test.fastq.gz"],
                    ["barid", "r2", "test_dir/test_2.fastq.gz"],
                    ["barid", "r1", "test_dir/test_3.fastq.gz"],
                ]
            )

        fastqs = parse_fastqs_map_file("test_map.csv")
        assert len(fastqs) == 2
        assert ("barid", "R1") in fastqs
        assert ("barid", "R2") in fastqs
        assert len(fastqs[("barid", "R1")]) == 2
        assert fastqs[("barid", "R1")][0] == "test_dir/test.fastq.gz"
        assert fastqs[("barid", "R1")][1] == "test_dir/test_3.fastq.gz"


def test_invalid_fastqs_map_file():
    """Test that error is raised if file is invalid."""
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
                    ["client_id", "r_notation", "path"],
                    ["barid", "r1", "test_dir/test.fastq.gz"],
                    ["barid", "r2", "test_dir/test_2.fastq.zip"],
                    ["barid", "r1", "test_dir/test_3.fastq.gz"],
                ]
            )
        try:
            parse_fastqs_map_file("test_map.csv")
        except ValidationError as err:
            assert "Bad file extension in path" in err.args[0]


def test_fastqs_map_file_path_does_not_exist():
    """Test that error is raised if file is invalid."""
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
                    ["client_id", "r_notation", "path"],
                    ["barid", "r1", "test_dir/test.fastq.gz"],
                    ["barid", "r1", "test_dir/test_3.fastq.gz"],
                    ["barid", "r1", "test_dir/i_dont_exist.fastq.gz"],
                ]
            )
        try:
            parse_fastqs_map_file("test_map.csv")
        except ValidationError as err:
            assert "Could not find" in err.args[0]


def test_fastqs_map_file_has_wrong_header():
    """Test that header is validated properly."""
    with open("test_map.csv", "w") as map_file:
        writer = csv.writer(map_file)
        writer.writerows(
            [
                ["client_id", "r1_notation", "path"],
                ["barid", "r1", "test_dir/test.fastq.gz"],
                ["barid", "r1", "test_dir/test_3.fastq.gz"],
                ["barid", "r1", "test_dir/i_dont_exist.fastq.gz"],
            ]
        )
    try:
        parse_fastqs_map_file("test_map.csv")
    except ValidationError as err:
        assert "Unexpected CSV header" in err.args[0]


def test__validate_header():
    """Test that header is validated properly."""
    header_row = dict(foo="foo", bar="bar")
    try:
        _validate_header(header_row)
    except ValidationError:
        pass

    header_row = dict(
        client_id="client_id", r_notation="r_notation", path="path"
    )
    assert _validate_header(header_row) is None


def test_is_valid_uuid__is_valid():
    """"Test that a UUID is a valid UUID"""
    assert is_valid_uuid("11111111-1111-1111-1111-111111111111")


def test_is_valid_uuid__is_not_valid__too_long():
    """"Test that UUID with extra chars is not a valid UUID"""
    assert is_valid_uuid("11111111-1111-1111-1111-11111111111122") is False


def test_is_valid_uuid__is_not_valid__too_short():
    """"Test that UUID with missing chars is not a valid UUID"""
    assert is_valid_uuid("11111111-1111-1111-1111-1") is False


def test_is_valid_uuid__is_not_valid__text():
    """"Test that random word is not a valid UUID"""
    assert is_valid_uuid("foo") is False
