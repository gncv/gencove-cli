"""Common command line options.

These options must be added to all commands.
"""
import os

import click

from gencove.constants import HOST

common_options = [  # pylint: disable=invalid-name
    click.option(
        "--host",
        default=lambda: os.environ.get("GENCOVE_HOST", HOST),
        help="Optional Gencove API host, including http/s protocol. "
        "Can be passed as GENCOVE_HOST environment variable. "
        f"Defaults to {HOST}",
    ),
    click.option(
        "--email",
        default=lambda: os.environ.get("GENCOVE_EMAIL", ""),
        help="Gencove user email to be used in login. "
        "Can be passed as GENCOVE_EMAIL environment variable",
    ),
    click.option(
        "--password",
        default=lambda: os.environ.get("GENCOVE_PASSWORD", ""),
        help="Gencove user password to be used in login. "
        "Can be passed as GENCOVE_PASSWORD environment variable",
    ),
    click.option(
        "--api-key",
        default=lambda: os.environ.get("GENCOVE_API_KEY", ""),
        help="Gencove api key. "
        "Can be passed as GENCOVE_API_KEY environment variable",
    ),
]


def add_options(options):  # pylint: disable=missing-function-docstring
    def _add_options(func):
        for option in reversed(options):
            func = option(func)
        return func

    return _add_options
