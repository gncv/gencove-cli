"""Python library which enables you to use Gencoves' research backend."""
import click

from gencove import version
from gencove.command.basespace import basespace
from gencove.command.download import download
from gencove.command.explorer import explorer
from gencove.command.files import list_file_types
from gencove.command.projects import projects
from gencove.command.reports import reports
from gencove.command.s3_imports import s3
from gencove.command.sample_manifests import sample_manifests
from gencove.command.samples import samples
from gencove.command.upload import upload
from gencove.command.uploads import uploads
from gencove.command.webhook import webhooks
from gencove.utils import python_version_check


def announcements():
    """Preamble announcements displayed whenever the CLI is called"""
    python_version_check()


@click.group()
@click.version_option(version=version.version())
def cli():
    """Gencove's command line interface."""


announcements()
cli.add_command(basespace)
cli.add_command(download)
cli.add_command(explorer)
cli.add_command(list_file_types)
cli.add_command(upload)
cli.add_command(uploads)
cli.add_command(projects)
cli.add_command(reports)
cli.add_command(samples)
cli.add_command(sample_manifests)
cli.add_command(s3)
cli.add_command(webhooks)

if __name__ == "__main__":
    cli()
