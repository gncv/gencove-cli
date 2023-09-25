"""Monthly usage shell command definition."""
import click

from gencove.command.common_cli_options import add_options, common_options
from gencove.command.utils import validate_destination_exists, validate_uuid
from gencove.constants import Credentials, Optionals

from .main import MonthlyUsageReport


@click.command("monthly-usage")
@click.argument("destination", callback=validate_destination_exists)
@add_options(common_options)
def monthly_usage(  # pylint: disable=too-many-arguments
    destination,
    host,
    email,
    password,
    api_key,
):
    """Get monthly usage report for organization.

    `DESTINATION`: path/to/save/manfiest/to
    """
    MonthlyUsageReport(
        destination,
        Credentials(email=email, password=password, api_key=api_key),
        Optionals(host=host),
    ).run()
