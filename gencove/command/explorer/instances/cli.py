"""Commands to be executed from command line."""
import click

from .inactivity_stop.cli import inactivity_stop


@click.group()
def instances():
    """Explorer instances management commands."""


instances.add_command(inactivity_stop)
