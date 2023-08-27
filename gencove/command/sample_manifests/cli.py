"""Commands to be executed from command line."""
# pylint: disable=E0012,C0330,R0913
import click

from .get_sample_manifest.cli import get_sample_manifest


@click.group()
def sample_manifests():
    """Sample manifest management commands."""


sample_manifests.add_command(get_sample_manifest)
