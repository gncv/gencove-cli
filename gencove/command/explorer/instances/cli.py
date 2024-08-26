"""Commands to be executed from command line."""
import click

from .inactivity_stop.cli import inactivity_stop
from .list.cli import list_instances
from .shell.cli import shell
from .start.cli import start
from .stop.cli import stop
from .url.cli import url


@click.group()
def instances():
    """Explorer instances management commands."""


instances.add_command(start)
instances.add_command(stop)
instances.add_command(list_instances)
instances.add_command(inactivity_stop)
instances.add_command(shell)
instances.add_command(url)
