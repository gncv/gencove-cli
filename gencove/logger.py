"""Utilities for different levels of click.echo outputs."""
import os

import click


INFO = "INFO"
DEBUG = "DEBUG"
LOG_LEVEL = os.environ.get("GENCOVE_LOG", INFO)


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
