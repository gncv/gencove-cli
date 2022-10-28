"""Commands to be executed from command line."""
# pylint: disable=E0012,C0330,R0913
import click

from .create.cli import create_project
from .create_batch.cli import create_project_batch
from .create_merged_vcf.cli import create_merged_vcf
from .delete_samples.cli import delete_project_samples
from .get_batch.cli import get_batch
from .get_merged_vcf.cli import get_merged_vcf
from .import_existing_samples.cli import import_existing_project_samples
from .list.cli import list_projects
from .list_batch_types.cli import list_project_batch_types
from .list_batches.cli import list_project_batches
from .list_pipeline_capabilities.cli import list_project_pipeline_capabilities
from .list_pipelines.cli import list_project_pipelines
from .restore_samples.cli import restore_project_samples
from .run_prefix.cli import run_prefix
from .samples.cli import list_project_samples
from .status_merged_vcf.cli import status_merged_vcf


@click.group()
def projects():
    """Project managements commands."""


projects.add_command(create_project)
projects.add_command(create_project_batch)
projects.add_command(list_projects)
projects.add_command(list_project_samples)
projects.add_command(list_project_batch_types)
projects.add_command(list_project_batches)
projects.add_command(list_project_pipeline_capabilities)
projects.add_command(list_project_pipelines)
projects.add_command(get_batch)
projects.add_command(delete_project_samples)
projects.add_command(restore_project_samples)
projects.add_command(import_existing_project_samples)
projects.add_command(run_prefix)
projects.add_command(create_merged_vcf)
projects.add_command(status_merged_vcf)
projects.add_command(get_merged_vcf)
