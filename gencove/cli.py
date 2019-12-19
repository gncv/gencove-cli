"""Python library which enables you to use Gencoves' research backend."""
import os

import click

from gencove import version
from gencove.command.download import (
    Download,
    DownloadFilters,
    DownloadOptions,
)
from gencove.command.upload import Upload, UploadOptions
from gencove.constants import Credentials, DOWNLOAD_TEMPLATE, HOST
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
@click.option(
    "--api-key",
    default=lambda: os.environ.get("GENCOVE_API_KEY", ""),
    help="Gencove api key. "
    "Can be passed as GENCOVE_API_KEY environment variable",
)
@click.option(
    "--run-project-id",
    default=None,
    help="Immediately assign all uploaded files to this project and run them",
)
def upload(  # pylint: disable=C0330,R0913
    source, destination, host, email, password, api_key, run_project_id
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

    Args:
        source (.fastq.gz, .fastq.bgz, .fq.gz, .fq.bgz):
            folder that contains fastq files to be uploaded
            OR .fastq-map.csv file
        destination (str, optional): 'gncv://' notated folder
            on Gencove's system, where the files will be uploaded to.
        run_project_id (UUID, optional): ID of a project to which all files
            in this upload will be assigned to and then immediately analyzed.
    """
    Upload(
        source,
        destination,
        Credentials(email, password, api_key),
        UploadOptions(host, run_project_id),
    ).run()


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
    "--api-key",
    default=lambda: os.environ.get("GENCOVE_API_KEY", ""),
    help="Gencove api key. "
    "Can be passed as GENCOVE_API_KEY environment variable",
)
@click.option(
    "--skip-existing/--no-skip-existing",
    default=True,
    help="Skip downloading files that already exist in DESTINATION",
)
@click.option(
    "--download-template",
    default=DOWNLOAD_TEMPLATE,
    help=(
        "Change downloads structure. "
        "Defaults to: {}".format(DOWNLOAD_TEMPLATE)
    ),
)
def download(  # pylint: disable=C0330,R0913
    destination,
    project_id,
    sample_ids,
    file_types,
    host,
    email,
    password,
    api_key,
    skip_existing,
    download_template,
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

    Args:
        destination (str): path/to/save/deliverables/to.
        project_id (str): project id in Gencove's system.
        sample_ids (list(str), optional): specific samples for which
            to download the results. if not specified, download deliverables
            for all samples.
        file_types (list(str), optional): specific deliverables to download
            results for. if not specified, all file types will be downloaded.
        skip_existing (bool, optional, default True): skip downloading existing
            files.
    """  # noqa: E501
    s_ids = tuple()
    if sample_ids:
        s_ids = tuple(s_id.strip() for s_id in sample_ids.split(","))
        echo_debug("Sample ids translation: {}".format(s_ids))

    f_types = tuple()
    if file_types:
        f_types = tuple(f_type.strip() for f_type in file_types.split(","))
        echo_debug("File types translation: {}".format(f_types))

    Download(
        destination,
        DownloadFilters(project_id, s_ids, f_types),
        Credentials(email, password, api_key),
        DownloadOptions(host, skip_existing, download_template),
    ).run()


if __name__ == "__main__":
    cli()
