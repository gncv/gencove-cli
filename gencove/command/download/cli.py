"""Commands to be executed from command line."""
import click

from gencove.command.common_cli_options import add_options, common_options
from gencove.constants import (
    Credentials,
    DOWNLOAD_TEMPLATE,
    DownloadTemplateParts,
)
from gencove.logger import echo_debug

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
    "--download-template",
    default=DOWNLOAD_TEMPLATE,
    help=(
        "Change downloads structure. Defaults to: {}."
        "\nAvailable tokens: \n{}".format(
            DOWNLOAD_TEMPLATE,
            "\n".join(
                [
                    "{{{}}}".format(v)
                    for v in DownloadTemplateParts._asdict().values()
                ]
            ),
        )
    ),
)
@add_options(common_options)
def download(  # pylint: disable=C0330,R0913
    destination,
    project_id,
    sample_ids,
    file_types,
    skip_existing,
    download_template,
    host,
    email,
    password,
    api_key,
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
