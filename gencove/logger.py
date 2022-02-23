"""Utilities for different levels of click.echo outputs."""
import logging
import os
import sys
import uuid
from datetime import datetime
from platform import platform

import boto3

import click

from gencove.version import version

INFO = "INFO"
DEBUG = "DEBUG"
LOG_LEVEL = os.environ.get("GENCOVE_LOG", INFO)
DEBUG_LOG = []


def _echo(msg, **kwargs):
    """Output click echo message."""
    if LOG_LEVEL == DEBUG:
        msg = f"{datetime.utcnow().isoformat()} {msg}"
    click.echo(msg, **kwargs)


def _log(msg):
    """Adds the message to the log list."""
    msg = f"{datetime.utcnow().isoformat()} {msg}"
    DEBUG_LOG.append(msg)


def output_warning(text):
    """Click echo warning."""
    return click.style(
        "WARNING: {}".format(text), fg="bright_yellow", bold=True
    )


def output_error(text):
    """Click echo error."""
    return click.style("ERROR: {}".format(text), fg="bright_red", bold=True)


def echo_data(msg, **kwargs):
    """Output click echo msg."""
    _echo(msg, **kwargs)
    _log(msg)


def echo_info(msg, **kwargs):
    """Output click echo msg."""
    _echo(msg, err=True, **kwargs)
    _log(msg)


def echo_debug(msg, **kwargs):
    """Output click echo msg only if debug is on."""
    if LOG_LEVEL == DEBUG:
        _echo(msg, err=True, **kwargs)
    _log(msg)


def echo_warning(msg, **kwargs):
    """Output click echo msg with background."""
    _echo(output_warning(msg), err=True, **kwargs)
    _log(msg)


def echo_error(msg, **kwargs):
    """Output click echo msg with background."""
    _echo(output_error(msg), err=True, **kwargs)
    _log(msg)


echo_debug(
    "Python version: {}.{}.{}".format(
        sys.version_info.major,
        sys.version_info.minor,
        sys.version_info.micro,
    )
)
echo_debug("CLI version: {}".format(version()))
echo_debug("OS details: {}".format(platform()))
echo_debug("boto3 version: {}".format(boto3.__version__))
if LOG_LEVEL == DEBUG:
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
    logging.getLogger("botocore.auth").setLevel(logging.CRITICAL)


def get_debug_file_name():
    """Creates a 'unique' file name YYYY_MM_DD_HH_MM_RANDOM_ID.log
    inside a YYYY_MM folder.
    """
    now = datetime.utcnow()
    timestamp = f"{now:%Y_%m_%d_%H_%M_%S}"
    random_id = str(uuid.uuid4())[:8]
    filename = f"{timestamp}_{random_id}.log"
    folder_name = f"{now:%Y_%m}"
    folder = os.path.join(".logs", folder_name)
    file_path = os.path.join(folder, filename)
    if not os.path.exists(folder):
        os.makedirs(folder)
    return file_path


def dump_debug_log():
    """Saves the logs into a file."""
    if os.environ.get("GENCOVE_SAVE_DUMP_LOG") != "FALSE":
        try:
            debug_filename = get_debug_file_name()
            log = "\n".join(DEBUG_LOG)
            with open(debug_filename, "w") as dump_file:
                dump_file.write(log)
            _echo(
                f"Please attach the debug log file located in {debug_filename} to a bug report."  # noqa: E501  # pylint: disable=line-too-long
            )
        except PermissionError:
            echo_warning(
                "An error occurred, but we couldn't write a debug log file to disk."  # noqa: E501  # pylint: disable=line-too-long
            )
