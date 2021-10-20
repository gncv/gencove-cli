"""List BaseSpace projects shell command definition.
"""
import click

from gencove.command.common_cli_options import add_options, common_options
from gencove.constants import Credentials, Optionals

from .main import BaseSpaceList


@click.command("list")
@add_options(common_options)
def basespace_list(
    host,
    email,
    password,
    api_key,
):
    """List all BaseSpace projects.

    Examples:

        Import Biosamples to a project:

            gencove basespace projects list

    """
    BaseSpaceList(
        Credentials(email=email, password=password, api_key=api_key),
        Optionals(host=host),
    ).run()
