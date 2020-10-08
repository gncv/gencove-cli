"""Commands to be executed from command line."""
import click

from .get_metadata.cli import get_metadata


@click.group()
def samples():
    """Sample managements commands."""


samples.add_command(get_metadata)
