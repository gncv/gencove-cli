"""Commands to be executed from command line."""
import click

from gencove.command.common_cli_options import add_options, common_options
from gencove.constants import Credentials, Optionals

from .list import List


@click.group()
def projects():
    """Project managements commands."""


@projects.command("list")
@add_options(common_options)
def list_projects(host, email, password, api_key):
    """List your projects."""
    List(Credentials(email, password, api_key), Optionals(host)).run()
