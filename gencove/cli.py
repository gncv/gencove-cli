"""Python library which enables you to use Gencoves' research backend."""
import os

import click

from gencove import version
from gencove.commands.upload import upload
from gencove.constants import HOST


@click.group()
@click.version_option(version=version.version())
def cli():
    """Gencove's command line interface."""


@cli.command()
@click.argument("source")
@click.argument("destination", required=False)
@click.option(
    "--host",
    default=HOST,
    help="Optional Gencove API host, including http/s protocol. "
    "Defaults to https://api.gencove.com",
)
@click.option(
    "--email",
    default=lambda: os.environ.get("GENCOVE_EMAIL", ""),
    help="Gencove user email to be used in login. "
    "Can be passed as GENCOVE_EMAIL environment variable",
)
@click.option(
    "--password",
    default=lambda: os.environ.get("GENCOVE_PASSWORD", ""),
    help="Gencove user password to be used in login. "
    "Can be passed as GENCOVE_PASSWORD environment variable",
)
def sync(source, destination, host, email, password):
    """Upload FASTQ files to Gencove's system.

    :param source: folder that contains fastq files to be uploaded.
    :type source: .fastq.gz, .fastq.bgz, .fq.gz, .fq.bgz
    :param destination: (optional) 'gncv://' notated folder
        on Gencove's system, where the files will be uploaded to.
    :type destination: str

    Example:
        `gencove sync test_dataset gncv://test`
    """
    upload(source, destination, host, email, password)


if __name__ == "__main__":
    cli()
