"""Copy existing samples shell command definition."""
import click

from gencove.command.common_cli_options import add_options, common_options
from gencove.command.utils import validate_uuid, validate_uuid_list
from gencove.constants import Credentials, Optionals

from .main import CopyExistingSamples


@click.command("copy-existing-samples")
@click.argument("project_id", callback=validate_uuid)
@click.option(
    "--source-project-id",
    "--project-id",
    required=False,
    help=(
        "Copy all available samples, in succeeded or failed_qc state that have"
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
        "A comma separated list of source sample ids to copy into the provided"
        " project."
        " Either --source-project-id or --source-sample-ids option must be provided,"
        " but not both."
    ),
    callback=validate_uuid_list,
)
@add_options(common_options)
def copy_existing_project_samples(  # pylint: disable=too-many-arguments
    project_id,
    source_project_id,
    source_sample_ids,
    host,
    email,
    password,
    api_key,
):  # pylint: disable=line-too-long
    """Copy existing samples to a project.

    `PROJECT_ID`: Gencove project ID

    Examples:

        Copy all available samples from source project:

            gencove projects copy-existing-samples d9eaa54b-aaac-4b85-92b0-0b564be6d7db --source-project-id d8eb0bb5-29ee-44ed-b681-0fc05a557183

        Copy samples by id:

            gencove projects copy-existing-samples d9eaa54b-aaac-4b85-92b0-0b564be6d7db --sample-ids 59f5c1fd-cce0-4c4c-90e2-0b6c6c525d71,7edee497-12b5-4a1d-951f-34dc8dce1c1d
    """  # noqa: E501
    CopyExistingSamples(
        project_id,
        source_project_id,
        source_sample_ids,
        Credentials(email=email, password=password, api_key=api_key),
        Optionals(host=host),
    ).run()
