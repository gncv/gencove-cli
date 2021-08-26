"""Commands to be executed from command line."""
# pylint: disable=E0012,C0330,R0913
import click

from .s3_import.cli import s3_import


@click.group()
def s3():  # pylint: disable=C0103
    """S3 imports managements commands."""


s3.add_command(s3_import)
