"""Python library which enables you to use Gencoves' research backend."""
import os

import click

from gencove import version
from gencove.command.download import Filters, Options, download_deliverables
from gencove.command.upload import upload_fastqs
from gencove.constants import Credentials, HOST
from gencove.logger import echo_debug


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
def upload(source, destination, host, email, password):  # noqa: D301
    """Upload FASTQ files to Gencove's system.

    SOURCE: folder that contains fastq files to be uploaded (acceptable file
    extensions are .fastq.gz, .fastq.bgz, .fq.gz, .fq.bgz)

    DESTINATION (optional): gncv://[folder], where the folder is the location
    on Gencove systems

    Example:

        gencove upload test_dataset gncv://test
    \f

    :param source: folder that contains fastq files to be uploaded.
    :type source: .fastq.gz, .fastq.bgz, .fq.gz, .fq.bgz
    :param destination: (optional) 'gncv://' notated folder
        on Gencove's system, where the files will be uploaded to.
    :type destination: str
    """
    upload_fastqs(source, destination, host, email, password)


@cli.command()
@click.argument("destination")
@click.option("--project-id", help="Gencove project ID")
@click.option(
    "--sample-ids",
    help="A comma separated list of sample ids for "
    "which to download the deliverables",
)
@click.option(
    "--file-types",
    help="A comma separated list of deliverable file types to download.",
)
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
@click.option(
    "--skip-existing/--no-skip-existing",
    default=True,
    help="Skip downloading files that already exist in DESTINATION",
)
def download(  # pylint: disable=C0330,R0913
    destination,
    project_id,
    sample_ids,
    file_types,
    host,
    email,
    password,
    skip_existing,
):  # noqa: D413,D301,D412 # pylint: disable=C0301
    """Download deliverables of a project.

    Must specify either project id or sample ids.

    Examples:

        Download all samples results:

        gencove download ./results --project-id d9eaa54b-aaac-4b85-92b0-0b564be6d7db

        Download some samples:

        gencove download ./results --sample-ids 59f5c1fd-cce0-4c4c-90e2-0b6c6c525d71,7edee497-12b5-4a1d-951f-34dc8dce1c1d

        Download specific deliverables:

        gencove download ./results --project-id d9eaa54b-aaac-4b85-92b0-0b564be6d7db --file-types alignment-bam,impute-vcf,fastq-r1,fastq-r2

    \f

    :param destination: path/to/save/deliverables/to.
    :type destination: str
    :param project_id: project id in Gencove's system.
    :type project_id: str
    :param sample_ids: specific samples for which to download the results.
    if not specified, download deliverables for all samples.
    :type sample_ids: list(str)
    :param file_types: specific deliverables to download results for.
    if not specified, all file types will be downloaded.
    :type file_types: list(str)
    :param skip_existing: skip downloading existing files
    :type skip_existing: bool
    """  # noqa: E501
    s_ids = tuple()
    if sample_ids:
        s_ids = tuple(s_id.strip() for s_id in sample_ids.split(","))
        echo_debug("Sample ids translation: {}".format(s_ids))

    f_types = tuple()
    if file_types:
        f_types = tuple(f_type.strip() for f_type in file_types.split(","))
        echo_debug("File types translation: {}".format(f_types))

    download_deliverables(
        destination,
        Filters(project_id, s_ids, f_types),
        Credentials(email, password),
        Options(host, skip_existing),
    )


if __name__ == "__main__":
    cli()
