"""Uploads commands to be executed from command line."""
import click

from .list.cli import list_uploads


@click.group()
def uploads():
    """Uploads management commands."""


uploads.add_command(list_uploads)
