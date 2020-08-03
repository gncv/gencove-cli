"""Project batch get shell command definition."""
import click

from gencove.command.common_cli_options import add_options, common_options
from gencove.constants import Credentials, Optionals

from .main import GetBatch


@click.command("get-batch")
@click.argument("batch_id")
@click.option(
    "--output-filename",
    help="Output filename for batch deliverable.",
    type=click.Path(),
    required=False,
    default=None,
)
@add_options(common_options)
# pylint: disable=too-many-arguments
def get_batch(batch_id, output_filename, host, email, password, api_key):
    """Get batch that is available for a project.
    """
    GetBatch(
        batch_id,
        output_filename,
        Credentials(email, password, api_key),
        Optionals(host),
    ).run()
