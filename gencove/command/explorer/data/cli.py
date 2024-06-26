"""Commands to be executed from command line."""
import click

from .archive.cli import archive
from .cp.cli import cp
from .ls.cli import ls
from .presign.cli import presign
from .restore.cli import restore
from .rm.cli import rm
from .sync.cli import sync


@click.group()
def data():
    """Explorer data management commands."""


data.add_command(archive)
data.add_command(ls)
data.add_command(cp)
data.add_command(restore)
data.add_command(rm)
data.add_command(sync)
data.add_command(presign)

if __name__ == "__main__":
    data()
