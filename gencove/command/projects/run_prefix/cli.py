"""Project assign all uploads from a prefix shell command definition."""
import click

from gencove.command.common_cli_options import add_options, common_options
from gencove.constants import Credentials

from .constants import RunPrefixOptionals
from .main import RunPrefix


@click.command("run-prefix")
@click.argument("project_id")
@click.argument("prefix")
@click.option(
    "--metadata-json",
    required=False,
    default=None,
    help=("Add metadata to all uploads to be assigned to a project."),
)
@add_options(common_options)
def run_prefix(  # pylint: disable=too-many-arguments
    project_id, prefix, metadata_json, host, email, password, api_key
):
    """Assign all uploads from a prefix to a project. Optionally add metadata
    to the samples.
    """
    RunPrefix(
        project_id,
        prefix,
        Credentials(email, password, api_key),
        RunPrefixOptionals(host, metadata_json),
    ).run()
