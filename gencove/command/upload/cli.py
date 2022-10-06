"""Commands to be executed from command line."""
import click

from gencove.command.common_cli_options import add_options, common_options
from gencove.constants import Credentials

from .constants import UploadOptions
from .main import Upload


@click.command()
@click.argument("source")
@click.argument("destination", required=False)
@add_options(common_options)
@click.option(
    "--run-project-id",
    default=None,
    help="Immediately assign all uploaded files to this project and run them",
)
@click.option(
    "--output",
    required=False,
    default=None,
    help="A destination where to store the resulting assignments.",
)
@click.option(
    "--no-progress",
    is_flag=True,
    help="If specified, no progress bar is shown.",
)
@click.option(
    "--metadata",
    required=False,
    default=None,
    help=(
        "Assign metadata to all samples created from uploads. "
        "Only compatible with --run-project-id."
    ),
)
def upload(  # pylint: disable=E0012,C0330,R0913
    source,
    destination,
    host,
    email,
    password,
    api_key,
    run_project_id,
    output,
    no_progress,
    metadata,
):  # noqa: D301
    """Upload FASTQ files to Gencove's system.

    SOURCE: folder that contains fastq files to be uploaded (acceptable file
    extensions are .fastq.gz, .fastq.bgz, .fq.gz, .fq.bgz), or .fastq-map.csv
    file with the mapping of R1/R2 files to related sample by client_id

    DESTINATION (optional): gncv://[folder], where the folder is the location
    on Gencove systems

    Examples:

        Upload directory contents:

            gencove upload test_dataset gncv://test

    \f
    .. ignore::
        Args:
            source (.fastq.gz, .fastq.bgz, .fq.gz, .fq.bgz):
                folder that contains fastq files to be uploaded
                OR .fastq-map.csv file
            destination (str, optional): 'gncv://' notated folder
                on Gencove's system, where the files will be uploaded to.
            run_project_id (UUID, optional): ID of a project to which all files
                in this upload will be assigned to and then immediately analyzed.
            output (str, optional): must be used with run_project_id. "-"
                redirects the JSON to STDOUT, and a name redirects the output to
                a file.
            no_progress (bool, optional, default False): do not show progress
                bar.
            metadata (str, optional): JSON metadata to be applied to all samples

    """
    Upload(
        source,
        destination,
        Credentials(email=email, password=password, api_key=api_key),
        UploadOptions(host=host, project_id=run_project_id, metadata=metadata),
        output,
        no_progress,
    ).run()
