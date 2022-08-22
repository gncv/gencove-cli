"""Import existing samples shell command definition."""
import click

from gencove.command.common_cli_options import add_options, common_options
from gencove.constants import Credentials

from .constants import ImportExistingSamplesOptionals
from .main import ImportExistingSamples


@click.command("import-existing-samples")
@click.argument("project_id")
@click.option(
    "--samples",
    required=True,
    help=(
        "JSON array of objects that each has key sample_id and value sample "
        "UUID and optional key client_id with value of a valid client_id."
    ),
)
@click.option(
    "--metadata-json",
    required=False,
    default=None,
    help="Add metadata to all samples that are to be imported into a project.",
)
@add_options(common_options)
def import_existing_project_samples(  # pylint: disable=too-many-arguments
    project_id,
    samples,
    metadata_json,
    host,
    email,
    password,
    api_key,
):
    """Import existing samples to a project."""
    ImportExistingSamples(
        project_id,
        samples,
        Credentials(email=email, password=password, api_key=api_key),
        ImportExistingSamplesOptionals(host=host, metadata_json=metadata_json),
    ).run()
