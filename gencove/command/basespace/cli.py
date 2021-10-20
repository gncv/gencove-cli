"""Commands to be executed from command line."""
# pylint: disable=E0012,C0330,R0913
import click

from .autoimports.cli import autoimports
from .biosamples.cli import biosamples
from .projects.cli import projects


@click.group()
def basespace():
    """BaseSpace managements commands."""


basespace.add_command(autoimports)
basespace.add_command(biosamples)
basespace.add_command(projects)
