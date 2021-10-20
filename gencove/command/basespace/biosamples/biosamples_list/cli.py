"""List Biosamples from BaseSpace project shell command definition.
"""
import click

from gencove.command.common_cli_options import add_options, common_options
from gencove.constants import Credentials, Optionals

from .main import BiosamplesList


@click.command("list")
@click.argument("basespace_project_id")
@add_options(common_options)
def biosamples_list(
    basespace_project_id,
    host,
    email,
    password,
    api_key,
):
    """List all Biosamples from BaseSpace project.

    Examples:

        List Biosamples of a BaseSpace project:

            gencove basespace biosamples list 12345678

        List Biosamples of a BaseSpace projects:

            gencove basespace biosamples list 12345678,87654321

    """
    BiosamplesList(
        basespace_project_id,
        Credentials(email=email, password=password, api_key=api_key),
        Optionals(host=host),
    ).run()
