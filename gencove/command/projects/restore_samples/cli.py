"""Project restore samples shell command definition."""
import click

from gencove.command.common_cli_options import add_options, common_options
from gencove.constants import Credentials, Optionals
from gencove.logger import echo_debug

from .main import RestoreSamples


@click.command("restore-samples")
@click.argument("project_id")
@click.option(
    "--sample-ids",
    default="",
    help=(
        "A comma separated list of sample ids which will be restored. If "
        "omitted, restores all archived samples in project."
    ),
)
@add_options(common_options)
def restore_project_samples(  # pylint: disable=too-many-arguments
    project_id,
    sample_ids,
    host,
    email,
    password,
    api_key,
):
    """Restore samples in a project."""
    sample_ids = (
        [s_id.strip() for s_id in sample_ids.split(",")] if sample_ids else []
    )
    echo_debug("Sample ids translation: {}".format(sample_ids))

    RestoreSamples(
        project_id,
        sample_ids,
        Credentials(email, password, api_key),
        Optionals(host),
    ).run()
