"""Project autoimport Biosamples from BaseSpace projects shell command
definition.
"""
import click

from gencove.command.common_cli_options import add_options, common_options
from gencove.constants import Credentials, Optionals

from .main import BaseSpaceAutoImportList


@click.command("list")
@add_options(common_options)
def autoimport_list(
    host,
    email,
    password,
    api_key,
):  # pylint: disable=line-too-long
    """Lists periodic import of BaseSpace projects (their Biosamples) jobs.

    Examples:

        List automatic import jobs of BaseSpace projects:

            gencove basespace autoimports list
    """  # noqa: E501

    BaseSpaceAutoImportList(
        Credentials(email=email, password=password, api_key=api_key),
        Optionals(host=host),
    ).run()
