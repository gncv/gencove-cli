"""Commands to be executed from command line."""
# pylint: disable=E0012,C0330,R0913
import click

from .basespace_import.cli import basespace_import
from .basespace_list.cli import basespace_list


@click.group()
def projects():
    """BaseSpace projects management commands."""


projects.add_command(basespace_import)
projects.add_command(basespace_list)
