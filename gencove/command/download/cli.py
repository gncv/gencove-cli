"""Commands to be executed from command line."""
import click

from gencove.command.common_cli_options import add_options, common_options
from gencove.constants import (
    Credentials,
    DOWNLOAD_TEMPLATE,
    DownloadTemplateParts,
)
from gencove.logger import echo_debug
from gencove.utils import enum_as_dict

from .constants import DownloadFilters, DownloadOptions
from .main import Download


@click.command(context_settings=dict(max_content_width=150))
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
    "--skip-existing/--no-skip-existing",
    default=True,
    help="Skip downloading files that already exist in DESTINATION",
)
@click.option(
    "--download-urls",
    help="Output a list of urls in a JSON format.",
    is_flag=True,
)
@click.option(
    "--download-template",
    default=DOWNLOAD_TEMPLATE,
    help=(
        "Change downloads structure. Defaults to: {}."
        "\nAvailable tokens: \n{}".format(
            DOWNLOAD_TEMPLATE,
            "\n".join(
                [f"{{{v}}}" for v in enum_as_dict(DownloadTemplateParts).values()]
            ),
        )
    ),
)
@add_options(common_options)
@click.option(
    "--no-progress",
    is_flag=True,
    help="If specified, no progress bar is shown.",
)
@click.option(
    "--checksums",
    is_flag=True,
    help="If specified, an additional checksum file will be downloaded for each deliverable.",  # noqa: E501 line too long pylint: disable=line-too-long
)
def download(  # pylint: disable=E0012,C0330,R0913
    destination,
    project_id,
    sample_ids,
    file_types,
    skip_existing,
    download_urls,
    download_template,
    host,
    email,
    password,
    api_key,
    no_progress,
    checksums,
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

        Skip download entirely and print out the deliverables as a JSON:

            gencove download - --project-id d9eaa54b-aaac-4b85-92b0-0b564be6d7db --download-urls

    \f
    .. ignore::
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
            download_urls (bool, optional): output the files available for a
                download. if the destination parameter is "-", it goes to the
                stdout.
            no_progress (bool, optional, default False): do not show progress
                bar.
            checksums (bool, optional, default False): download additonal checksum
                files for each deliverable.

    """  # noqa: E501
    s_ids = tuple()
    if sample_ids:
        s_ids = tuple(s_id.strip() for s_id in sample_ids.split(","))
        echo_debug(f"Sample ids translation: {s_ids}")

    f_types = tuple()
    if file_types:
        f_types = tuple(f_type.strip() for f_type in file_types.split(","))
        echo_debug(f"File types translation: {f_types}")

    Download(
        destination,
        DownloadFilters(project_id=project_id, sample_ids=s_ids, file_types=f_types),
        Credentials(email=email, password=password, api_key=api_key),
        DownloadOptions(
            host=host,
            skip_existing=skip_existing,
            download_template=download_template,
        ),
        download_urls,
        no_progress,
        checksums,
    ).run()
