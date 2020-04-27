"""List projects shell command definition."""
import click

from gencove.command.common_cli_options import add_options, common_options
from gencove.constants import Credentials, Optionals

from .main import List


@click.command("list")
@add_options(common_options)
def list_projects(host, email, password, api_key):
    """List your projects."""
    List(Credentials(email, password, api_key), Optionals(host)).run()
