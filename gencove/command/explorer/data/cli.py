"""Commands to be executed from command line."""
import click

from .ls.cli import ls

# from .cp.cli import cp
# from .rm.cli import rm
# from .sync.cli import sync


@click.group()
def data():
    """Explorer instances management commands."""


data.add_command(ls)
# data.add_command(cp)
# data.add_command(rm)
# data.add_command(sync)
