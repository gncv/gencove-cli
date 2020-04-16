"""Commands to be executed from command line."""
# pylint: disable=C0330,R0913
import click

from .list.cli import list_projects
from .samples.cli import list_project_samples


@click.group()
def projects():
    """Project managements commands."""


projects.add_command(list_projects)
projects.add_command(list_project_samples)
