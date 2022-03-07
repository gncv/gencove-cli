"""Tests for loggers of Gencove CLI."""
import os

from click.testing import CliRunner

from gencove.logger import _log, dump_debug_log


def test_dump_debug_log(dump_filename):
    """Tests that the logs sent to _log are saved into a file when calling
    dump_debug_log.
    """
    del os.environ["GENCOVE_SAVE_DUMP_LOG"]
    logs = [f"log{i}" for i in range(100)]
    for msg in logs:
        _log(msg)
    runner = CliRunner()
    with runner.isolated_filesystem():
        dump_debug_log()
        with open(dump_filename, encoding="utf8") as log_file:
            log_content = log_file.read()
            assert all(log in log_content for log in logs)
