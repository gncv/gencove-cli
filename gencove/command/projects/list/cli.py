"""List projects shell command definition."""
import click

from gencove.command.common_cli_options import add_options, common_options
from gencove.constants import Credentials, Optionals

from .main import List


@click.command("list")
@click.option(
    "--include-capability/--no-include-capability",
    help="Include capability id and key",
    is_flag=True,
)
@add_options(common_options)
def list_projects(include_capability, host, email, password, api_key):
    """List your projects."""
    List(
        include_capability,
        Credentials(email=email, password=password, api_key=api_key),
        Optionals(host=host),
    ).run()
