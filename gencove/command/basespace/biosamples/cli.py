"""Commands to be executed from command line."""
# pylint: disable=E0012,C0330,R0913
import click

from .biosamples_list.cli import biosamples_list


@click.group()
def biosamples():
    """BaseSpace Biosamples management commands."""


biosamples.add_command(biosamples_list)
