"""Commands to be executed from command line."""
import click

from .verify.cli import verify


@click.group()
def webhook():
    """Webhook managements commands."""


webhook.add_command(verify)
