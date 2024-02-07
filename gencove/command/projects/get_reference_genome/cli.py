"""Commands to be executed from command line."""
import click

from gencove.command.common_cli_options import add_options, common_options
from gencove.command.projects.get_reference_genome.main import GetReferenceGenome
from gencove.command.utils import validate_uuid
from gencove.constants import Credentials, Optionals
from gencove.logger import echo_debug


@click.command("get-reference-genome")
@click.argument("project_id", callback=validate_uuid)
@click.argument(
    "destination",
    type=click.Path(file_okay=False),
)
@click.option(
    "--file-types",
    help=(
        "A comma separated list of deliverable file types to download. "
        "If not specified, all file types will be downloaded."
    ),
)
@add_options(common_options)
@click.option(
    "--no-progress",
    is_flag=True,
    help="If specified, no progress bar is shown.",
)
def get_reference_genome(
    project_id,
    destination,
    file_types,
    host,
    email,
    password,
    api_key,
    no_progress,
):
    """Download Reference genomes of a project

    `PROJECT_ID`: Gencove project ID
    `DESTINATION`: path/to/save/deliverables/to

    Examples:

        Download all reference genome files:

            gencove projects get_reference_genome d9eaa54b-aaac-4b85-92b0-0b564be6d7db
             ./genome


        Download only fasta reference genome file:

            gencove projects get_reference_genome d9eaa54b-aaac-4b85-92b0-0b564be6d7db
             . --file-types genome-fasta
    """
    f_types = tuple()
    if file_types:
        f_types = tuple(f_type.strip() for f_type in file_types.split(","))
        echo_debug(f"File types translation: {f_types}")
    GetReferenceGenome(
        project_id,
        destination,
        f_types,
        Credentials(email=email, password=password, api_key=api_key),
        Optionals(host=host),
        no_progress,
    ).run()
