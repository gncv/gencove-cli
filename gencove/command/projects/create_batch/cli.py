"""Project batch types list shell command definition."""
import click

from gencove.command.common_cli_options import add_options, common_options
from gencove.command.utils import validate_uuid, validate_uuid_list
from gencove.constants import Credentials, Optionals

from .main import CreateBatch


@click.command("create-batch")
@click.argument("project_id", callback=validate_uuid)
@click.option(
    "--batch-type",
    help="One of available project's batch types.\n"
    "Use `gencove projects list-batch-types` command to find out "
    "which batch types are available.",
)
@click.option("--batch-name", help="User defined batch name.")
@click.option(
    "--sample-ids",
    default="",
    help="A comma separated list of sample ids for "
    "which to create a batch; if not specified use all samples in project",
    callback=validate_uuid_list,
)
@add_options(common_options)
def create_project_batch(  # pylint: disable=too-many-arguments
    project_id,
    batch_type,
    batch_name,
    sample_ids,
    host,
    email,
    password,
    api_key,
):
    """Create a batch in a project.

    `PROJECT_ID`: Gencove project ID
    """
    CreateBatch(
        project_id,
        batch_type,
        batch_name,
        sample_ids,
        Credentials(email=email, password=password, api_key=api_key),
        Optionals(host=host),
    ).run()
