"""Utilities for different levels of click.echo outputs."""
import os

import click


INFO = "INFO"
DEBUG = "DEBUG"
LOG_LEVEL = os.environ.get("GENCOVE_LOG", INFO)

if LOG_LEVEL == DEBUG:
    import sys
    import logging
    from platform import platform
    import boto3
    from gencove.version import version

    click.echo(
        "Python version: {}.{}.{}".format(
            sys.version_info.major,
            sys.version_info.minor,
            sys.version_info.micro,
        )
    )
    click.echo("CLI version: {}".format(version()))
    click.echo("OS details: {}".format(platform()))
    click.echo("boto3 version: {}".format(boto3.__version__))
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


def output_warning(text):
    """Click echo warning."""
    return click.style(
        "WARNING: {}".format(text), bg="red", fg="white", bold=True
    )


def echo(msg, **kwargs):
    """Output click echo msg."""
    click.echo(msg, **kwargs)


def echo_debug(msg, **kwargs):
    """Output click echo msg only if debug is on."""
    if LOG_LEVEL == DEBUG:
        click.echo(msg, **kwargs)


def echo_warning(msg, **kwargs):
    """Output click echo msg with background."""
    echo(output_warning(msg), **kwargs)
