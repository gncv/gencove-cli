"""Configure inactivity stop for explorer instances command definition.
"""
import click

from gencove.command.common_cli_options import add_options, common_options
from gencove.constants import Credentials, Optionals

from .main import StopInstanceInactivity


@click.command("inactivity-stop")
@click.option(
    "--hours",
    default=None,
    help=(
        "Amount of hours of inactivity to wait before stopping instances. "
        "If hours == 0 then the instances are not stopped. "
        "If hours == None then the org-level config is applied."
    ),
)
@click.option(
    "--organization",
    is_flag=True,
    help="Sets the config for the entire Organization.",
)
@click.option(
    "--override",
    default=None,
    type=bool,
    help="Organization config overrides the instances configs.",
)
@add_options(common_options)
def inactivity_stop(  # pylint: disable=too-many-arguments
    hours: str,
    organization: bool,
    override: bool,
    host,
    email,
    password,
    api_key,
):  # pylint: disable=line-too-long
    """Stop instances after hours of inactivity.
    An instance can be configured to be stopped after some time of inactivity.
    Aditionally, this configuration can also be set at an Organization-level.
    By default the instance configuration has precedence over the org-level config,
    but this can be changed with the --override flag.
    """  # noqa: E501
    StopInstanceInactivity(
        hours,
        organization,
        override,
        Credentials(email=email, password=password, api_key=api_key),
        Optionals(host=host),
    ).run()
