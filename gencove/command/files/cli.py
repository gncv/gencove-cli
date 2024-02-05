"""Commands to be executed from command line."""
import click

from gencove.command.common_cli_options import add_options, common_options
from gencove.constants import Credentials, FileTypesObject, Optionals
from gencove.utils import enum_as_dict

from .main import ListFileTypes


@click.command("file-types")
@click.option("--project-id", required=False, help="Gencove project ID", type=str)
@click.option(
    "--object",
    "object_param",
    required=False,
    help="File types of a specific object",
    type=click.Choice(enum_as_dict(FileTypesObject).values()),
    default=FileTypesObject.SAMPLE.value,
)
@add_options(common_options)
def list_file_types(project_id, object_param, host, email, password, api_key):
    """List file types in Gencove's system."""
    ListFileTypes(
        project_id,
        object_param,
        Credentials(email=email, password=password, api_key=api_key),
        Optionals(host=host),
    ).run()
