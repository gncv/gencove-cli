"""Generate shareable Explorer URL"""
import click

from gencove.command.common_cli_options import add_options, common_options
from gencove.constants import Credentials, Optionals

from .main import GetInstanceURL


@click.command("url")
@add_options(common_options)
def url(  # pylint: disable=too-many-arguments
    host,
    email,
    password,
    api_key,
):  # pylint: disable=line-too-long
    """Generate shareable URL for Explorer instance."""  # noqa: E501
    GetInstanceURL(
        Credentials(email=email, password=password, api_key=api_key),
        Optionals(host=host),
    ).run()
