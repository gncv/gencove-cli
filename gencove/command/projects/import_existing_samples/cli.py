"""Import existing samples shell command definition."""
import click

from gencove.command.common_cli_options import add_options, common_options
from gencove.command.utils import validate_uuid, validate_uuid_list
from gencove.constants import Credentials
from gencove.logger import echo_debug

from .constants import ImportExistingSamplesOptionals
from .main import ImportExistingSamples


@click.command("import-existing-samples")
@click.argument("project_id", callback=validate_uuid)
@click.option(
    "--source-project-id",
    "--project-id",
    required=False,
    help=(
        "Import all available samples, in succeeded or failed_qc state that have"
        " files, from source project."
        " Either --source-project-id or --source-sample-ids option must be provided,"
        " but not both."
    ),
)
@click.option(
    "--source-sample-ids",
    "--sample-ids",
    required=False,
    help=(
        "A comma separated list of source sample ids to import into the provided"
        " project."
        " Either --source-project-id or --source-sample-ids option must be provided,"
        " but not both."
    ),
    callback=validate_uuid_list,
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
    source_project_id,
    source_sample_ids,
    metadata_json,
    host,
    email,
    password,
    api_key,
):  # pylint: disable=line-too-long
    """Import existing samples to a project.

    `PROJECT_ID`: Gencove project ID

    Examples:

        Import samples from project:

            gencove projects import-existing-samples d9eaa54b-aaac-4b85-92b0-0b564be6d7db --source-project-id d8eb0bb5-29ee-44ed-b681-0fc05a557183

        Import samples:

            gencove projects import-existing-samples d9eaa54b-aaac-4b85-92b0-0b564be6d7db --sample-ids 59f5c1fd-cce0-4c4c-90e2-0b6c6c525d71,7edee497-12b5-4a1d-951f-34dc8dce1c1d

        Import samples with metadata:

            gencove projects import-existing-samples d9eaa54b-aaac-4b85-92b0-0b564be6d7db --sample-ids 59f5c1fd-cce0-4c4c-90e2-0b6c6c525d71,7edee497-12b5-4a1d-951f-34dc8dce1c1d --metadata-json='{"batch": "batch1"}'
    """  # noqa: E501
    echo_debug(f"Sample ids translation: {source_sample_ids}")
    ImportExistingSamples(
        project_id,
        source_project_id,
        source_sample_ids,
        Credentials(email=email, password=password, api_key=api_key),
        ImportExistingSamplesOptionals(host=host, metadata_json=metadata_json),
    ).run()
