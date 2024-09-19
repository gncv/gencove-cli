"""Project hide samples shell command definition."""
import click

from gencove.command.common_cli_options import add_options, common_options
from gencove.command.utils import validate_uuid, validate_uuid_list
from gencove.constants import Credentials, Optionals
from gencove.logger import echo_debug

from .main import HideSamples


@click.command("hide-samples")
@click.argument("project_id", callback=validate_uuid)
@click.option(
    "--sample-ids",
    default="",
    help=("A comma separated list of sample ids which will be hidden."),
    callback=validate_uuid_list,
)
@add_options(common_options)
def hide_project_samples(  # pylint: disable=too-many-arguments
    project_id,
    sample_ids,
    host,
    email,
    password,
    api_key,
):
    """Hide samples in a project.

    `PROJECT_ID`: Gencove project ID
    """
    echo_debug(f"Sample ids translation: {sample_ids}")

    HideSamples(
        project_id,
        sample_ids,
        Credentials(email=email, password=password, api_key=api_key),
        Optionals(host=host),
    ).run()
