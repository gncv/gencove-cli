"""Commands to be executed from command line."""
# pylint: disable=E0012,C0330,R0913
import click

from .autoimport_list.cli import autoimport_list
from .create.cli import create


@click.group()
def autoimports():
    """BaseSpace autoimports management commands."""


autoimports.add_command(autoimport_list)
autoimports.add_command(create)
