"""Python library which enables you to use Gencoves' research backend."""
import click

from gencove import version
from gencove.command.download import download
from gencove.command.projects import projects
from gencove.command.samples import samples
from gencove.command.upload import upload
from gencove.command.uploads import uploads


@click.group()
@click.version_option(version=version.version())
def cli():
    """Gencove's command line interface."""


cli.add_command(download)
cli.add_command(upload)
cli.add_command(uploads)
cli.add_command(projects)
cli.add_command(samples)


if __name__ == "__main__":
    cli()
