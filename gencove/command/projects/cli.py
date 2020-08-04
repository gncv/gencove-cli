"""Commands to be executed from command line."""
# pylint: disable=C0330,R0913
import click

from .create_batch.cli import create_project_batch
from .get_batch.cli import get_batch
from .list.cli import list_projects
from .list_batch_types.cli import list_project_batch_types
from .list_batches.cli import list_project_batches
from .samples.cli import list_project_samples


@click.group()
def projects():
    """Project managements commands."""


projects.add_command(create_project_batch)
projects.add_command(list_projects)
projects.add_command(list_project_samples)
projects.add_command(list_project_batch_types)
projects.add_command(list_project_batches)
projects.add_command(get_batch)
