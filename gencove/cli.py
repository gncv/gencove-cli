"""Python library which enables you to use Gencoves' research backend."""
import click

from gencove import version
from gencove.command.basespace import basespace
from gencove.command.download import download
from gencove.command.files import list_file_types
from gencove.command.projects import projects
from gencove.command.s3_imports import s3
from gencove.command.samples import samples
from gencove.command.upload import upload
from gencove.command.uploads import uploads
from gencove.command.webhook import webhooks


@click.group()
@click.version_option(version=version.version())
def cli():
    """Gencove's command line interface."""


cli.add_command(basespace)
cli.add_command(download)
cli.add_command(list_file_types)
cli.add_command(upload)
cli.add_command(uploads)
cli.add_command(projects)
cli.add_command(samples)
cli.add_command(s3)
cli.add_command(webhooks)


if __name__ == "__main__":
    cli()
