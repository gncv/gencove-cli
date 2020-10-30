"""Utilities for different levels of click.echo outputs."""
import os
from datetime import datetime

import click


INFO = "INFO"
DEBUG = "DEBUG"
LOG_LEVEL = os.environ.get("GENCOVE_LOG", INFO)


def _echo_with_datetime(msg, **kwargs):
    """Output click echo message with datetime."""
    click.echo("{}  {}".format(datetime.utcnow().isoformat(), msg), **kwargs)


def _echo(msg, **kwargs):
    """Output click echo message without datetime."""
    click.echo(msg, **kwargs)


if LOG_LEVEL == DEBUG:
    import sys
    import logging
    from platform import platform
    import boto3
    from gencove.version import version

    _echo_with_datetime(
        "Python version: {}.{}.{}".format(
            sys.version_info.major,
            sys.version_info.minor,
            sys.version_info.micro,
        )
    )
    _echo_with_datetime("CLI version: {}".format(version()))
    _echo_with_datetime("OS details: {}".format(platform()))
    _echo_with_datetime("boto3 version: {}".format(boto3.__version__))
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
    logging.getLogger("botocore.auth").setLevel(logging.CRITICAL)


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
    if LOG_LEVEL == DEBUG:
        _echo_with_datetime(msg, **kwargs)
    else:
        _echo(msg, **kwargs)


def echo_info(msg, **kwargs):
    """Output click echo msg."""
    if LOG_LEVEL == DEBUG:
        _echo_with_datetime(msg, err=True, **kwargs)
    else:
        _echo(msg, err=True, **kwargs)


def echo_debug(msg, **kwargs):
    """Output click echo msg only if debug is on."""
    if LOG_LEVEL == DEBUG:
        _echo_with_datetime(msg, err=True, **kwargs)


def echo_warning(msg, **kwargs):
    """Output click echo msg with background."""
    if LOG_LEVEL == DEBUG:
        _echo_with_datetime(output_warning(msg), err=True, **kwargs)
    else:
        _echo(output_warning(msg), err=True, **kwargs)


def echo_error(msg, **kwargs):
    """Output click echo msg with background."""
    if LOG_LEVEL == DEBUG:
        _echo_with_datetime(output_error(msg), err=True, **kwargs)
    else:
        _echo(output_error(msg), err=True, **kwargs)
