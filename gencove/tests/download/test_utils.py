"""Tests for download utilities."""
# pylint: disable=wrong-import-order, import-error, protected-access

import os

from click.testing import CliRunner

from gencove.command.download.constants import MEGABYTE
from gencove.command.download.utils import (
    _ThreadSafeCounter,
    _build_ranges,
    _create_filepath,
    _determine_parallel_workers,
    _extract_total_size,
    _finalize_download,
    _get_prefix_parts,
    deliverable_type_from_filename,
    get_download_template_format_params,
    get_filename_from_download_url,
)
from gencove.constants import DownloadTemplateParts

from pydantic import HttpUrl


def test_get_filename_from_download_url_with_query_param():
    """Test extracting filename from URL with response-content-disposition."""
    url = "https://example.com/file.txt?response-content-disposition=attachment%3B+filename%3Dtest_file.fastq.gz"  # noqa E501 pylint: disable=line-too-long
    result = get_filename_from_download_url(url)
    assert result == "test_file.fastq.gz"


def test_get_filename_from_download_url_without_query_param():
    """Test extracting filename from URL path when no query param."""
    url = "https://example.com/path/to/sample.fastq.gz"
    result = get_filename_from_download_url(url)
    assert result == "sample.fastq.gz"


def test_get_filename_from_download_url_with_httpurl():
    """Test extracting filename from pydantic HttpUrl object."""
    url = HttpUrl("https://example.com/path/to/file.vcf.gz")
    result = get_filename_from_download_url(url)
    assert result == "file.vcf.gz"


def test_deliverable_type_from_filename():
    """Test extracting file type from filename."""
    assert deliverable_type_from_filename("sample.fastq.gz") == "fastq.gz"
    assert deliverable_type_from_filename("file.vcf.gz") == "vcf.gz"
    assert deliverable_type_from_filename("data.tar.gz.bz2") == "tar.gz.bz2"
    assert deliverable_type_from_filename("simple.txt") == "txt"


def test_create_filepath():
    """Test file path creation with directory structure."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = _create_filepath(".", "test_dir/nested", "file.txt")
        assert result == "./test_dir/nested/file.txt"
        assert os.path.exists("./test_dir/nested")


def test_create_filepath_no_prefix():
    """Test file path creation without prefix directories."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = _create_filepath("output", "", "sample.fastq.gz")
        assert result == "output/sample.fastq.gz"
        assert os.path.exists("output")


def test_get_prefix_parts_with_dirs():
    """Test parsing prefix with directory structure."""
    full_prefix = "client_id/gencove_id/{default_filename}"
    result = _get_prefix_parts(full_prefix)
    assert result.dirs == "client_id/gencove_id"
    assert result.filename == "{default_filename}"
    assert result.file_extension == ""
    assert result.use_default_filename is True


def test_get_prefix_parts_with_extension():
    """Test parsing prefix with file extension."""
    full_prefix = "prefix/path/{file_type}.vcf.gz"
    result = _get_prefix_parts(full_prefix)
    assert result.dirs == "prefix/path"
    assert result.filename == "{file_type}"
    assert result.file_extension == "vcf.gz"


def test_get_prefix_parts_no_dirs():
    """Test parsing prefix without directories."""
    full_prefix = "{client_id}_{file_type}"
    result = _get_prefix_parts(full_prefix)
    assert result.dirs == ""
    assert result.filename == "{client_id}_{file_type}"
    assert result.file_extension == ""


def test_determine_parallel_workers_small_file():
    """Test worker count for files smaller than minimum part size."""
    # 5 MB file should use 1 worker
    total = 5 * MEGABYTE
    assert _determine_parallel_workers(total) == 1


def test_determine_parallel_workers_medium_file():
    """Test worker count for medium-sized files."""
    # 40 MB file should use 5 workers (40/8 = 5)
    total = 40 * MEGABYTE
    assert _determine_parallel_workers(total) == 5


def test_determine_parallel_workers_large_file():
    """Test worker count capped at MAX_PARALLEL_DOWNLOADS."""
    # 200 MB file needs >8 workers but is capped at 8
    total = 200 * MEGABYTE
    assert _determine_parallel_workers(total) == 8


def test_build_ranges_single_worker():
    """Test range building with single worker."""
    total = 1000
    worker_count = 1
    ranges = _build_ranges(total, worker_count)
    assert len(ranges) == 1
    assert ranges[0] == (0, 999)


def test_build_ranges_multiple_workers():
    """Test range building with multiple workers."""
    total = 1000
    worker_count = 4
    ranges = _build_ranges(total, worker_count)
    assert len(ranges) == 4
    assert ranges[0] == (0, 249)
    assert ranges[1] == (250, 499)
    assert ranges[2] == (500, 749)
    assert ranges[3] == (750, 999)


def test_build_ranges_uneven_split():
    """Test range building when total doesn't divide evenly."""
    total = 1005
    worker_count = 4
    ranges = _build_ranges(total, worker_count)
    assert len(ranges) == 4
    assert ranges[-1][1] == 1004  # last byte


def test_finalize_download():
    """Test finalizing download by renaming temp file."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("file.tmp", "w", encoding="utf-8") as tmp:
            tmp.write("test content")

        _finalize_download("file.tmp", "file.txt")

        assert not os.path.exists("file.tmp")
        assert os.path.exists("file.txt")
        with open("file.txt", "r", encoding="utf-8") as final:
            assert final.read() == "test content"


def test_finalize_download_replaces_existing():
    """Test that finalize_download replaces existing destination file."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("file.tmp", "w", encoding="utf-8") as tmp:
            tmp.write("new content")
        with open("file.txt", "w", encoding="utf-8") as existing:
            existing.write("old content")

        _finalize_download("file.tmp", "file.txt")

        assert not os.path.exists("file.tmp")
        assert os.path.exists("file.txt")
        with open("file.txt", "r", encoding="utf-8") as final:
            assert final.read() == "new content"


def test_thread_safe_counter_increment():
    """Test thread-safe counter increments correctly."""
    counter = _ThreadSafeCounter()
    assert counter.value == 0

    result = counter.increment(10)
    assert result == 10
    assert counter.value == 10

    result = counter.increment(5)
    assert result == 15
    assert counter.value == 15


def test_extract_total_size_from_content_length():
    """Test extracting size from Content-Length header."""
    headers = {"content-length": "12345"}
    result = _extract_total_size(headers)
    assert result == 12345


def test_extract_total_size_from_content_range():
    """Test extracting size from Content-Range header."""
    headers = {"content-range": "bytes 0-999/5000", "content-length": "1000"}
    result = _extract_total_size(headers)
    assert result == 5000


def test_get_download_template_format_params():
    """Test getting download template format parameters."""
    client_id = "test_client"
    gencove_id = "test_gencove_id"

    result = get_download_template_format_params(client_id, gencove_id)

    assert result[DownloadTemplateParts.CLIENT_ID.value] == "test_client"
    assert result[DownloadTemplateParts.GENCOVE_ID.value] == "test_gencove_id"
    assert result[DownloadTemplateParts.FILE_TYPE.value] == "{file_type}"
    assert result[DownloadTemplateParts.FILE_EXTENSION.value] == "{file_extension}"
    assert result[DownloadTemplateParts.DEFAULT_FILENAME.value] == "{default_filename}"


def test_get_download_template_format_params_with_special_chars():
    """Test format params with special characters in IDs."""
    client_id = "client-123_test"
    gencove_id = "11111111-1111-1111-1111-111111111111"

    result = get_download_template_format_params(client_id, gencove_id)

    assert result[DownloadTemplateParts.CLIENT_ID.value] == "client-123_test"
    assert (
        result[DownloadTemplateParts.GENCOVE_ID.value]
        == "11111111-1111-1111-1111-111111111111"
    )
