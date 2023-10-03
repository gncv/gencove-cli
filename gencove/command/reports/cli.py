"""Commands to be executed from command line."""
# pylint: disable=E0012,C0330,R0913
import click

from .monthly_usage.cli import monthly_usage
from .project_qc.cli import project_qc


@click.group()
def reports():
    """Report management commands."""


reports.add_command(project_qc)
reports.add_command(monthly_usage)
