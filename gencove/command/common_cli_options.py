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
        default="",
        help="Gencove user email to be used in login. "
        "Can be passed as GENCOVE_EMAIL environment variable.",
    ),
    click.option(
        "--password",
        default="",
        help="Gencove user password to be used in login. "
        "Can be passed as GENCOVE_PASSWORD environment variable. "
        "When MFA is configured, an MFA token will have to be provided after "
        "the command is executed. Only used if --email is provided.",
    ),
    click.option(
        "--api-key",
        default="",
        help="Gencove api key. "
        "Can be passed as GENCOVE_API_KEY environment variable. "
        "When using the API key, an MFA token does not need to be provided.",
    ),
]


def add_options(options):  # pylint: disable=missing-function-docstring
    def _add_options(func):
        for option in reversed(options):
            func = option(func)
        return func

    return _add_options
