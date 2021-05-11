"""Commands to be executed from command line."""
import click

from .verify.cli import verify


@click.group()
def webhooks():
    """Webhook managements commands."""


webhooks.add_command(verify)
