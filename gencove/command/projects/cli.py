"""Commands to be executed from command line."""
# pylint: disable=E0012,C0330,R0913
import click

from .create_batch.cli import create_project_batch
from .create_merged_vcf.cli import create_merged_vcf
from .get_batch.cli import get_batch
from .get_merged_vcf.cli import get_merged_vcf
from .list.cli import list_projects
from .list_batch_types.cli import list_project_batch_types
from .list_batches.cli import list_project_batches
from .restore_samples.cli import restore_project_samples
from .samples.cli import list_project_samples
from .status_merged_vcf.cli import status_merged_vcf


@click.group()
def projects():
    """Project managements commands."""


projects.add_command(create_project_batch)
projects.add_command(list_projects)
projects.add_command(list_project_samples)
projects.add_command(list_project_batch_types)
projects.add_command(list_project_batches)
projects.add_command(get_batch)
projects.add_command(restore_project_samples)
projects.add_command(create_merged_vcf)
projects.add_command(status_merged_vcf)
projects.add_command(get_merged_vcf)
