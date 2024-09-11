"""Generate shareable Explorer URL"""
import click

from gencove.command.common_cli_options import add_options, common_options
from gencove.constants import Credentials, Optionals

from .main import GetInstanceURL


@click.command("url")
@click.option(
    "--expiration-hours",
    default=24,
    help=("Number of hours before the URL expires. Maximum is 24 hours."),
)
@add_options(common_options)
def url(  # pylint: disable=too-many-arguments
    expiration_hours: int,
    host: str,
    email: str,
    password: str,
    api_key: str,
):  # pylint: disable=line-too-long
    """Generate shareable URL for Explorer instance."""  # noqa: E501
    GetInstanceURL(
        expiration_hours,
        Credentials(email=email, password=password, api_key=api_key),
        Optionals(host=host),
    ).run()
