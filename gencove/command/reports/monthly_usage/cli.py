"""Monthly usage shell command definition."""
import click

from gencove.command.common_cli_options import add_options, common_options
from gencove.constants import Credentials, Optionals

from .main import MonthlyUsageReport


@click.command("monthly-usage")
@click.option(
    "--from",
    "from_",
    help="Date to start report from in format YYYY-MM, e.g. 2023-01. "
    "If supplied, --to parameter must also be supplied.",
    type=str,
    default=None,
    required=False,
)
@click.option(
    "--to",
    help="Date to end report at in format YYYY-MM, e.g. 2023-03. "
    "If supplied, --from parameter must also be supplied.",
    type=str,
    default=None,
    required=False,
)
@click.option(
    "--output-filename",
    help="Output filename for the output report. "
    "If not supplied, will download the file to the current directory.",
    type=click.Path(),
    default=None,
    required=False,
)
@add_options(common_options)
def monthly_usage(  # pylint: disable=too-many-arguments,invalid-name
    from_,
    to,
    output_filename,
    host,
    email,
    password,
    api_key,
):
    """Get monthly usage report for organization.
    If --to and --from parameters are not supplied,
    the last 12 months of usage are retrieved."""
    MonthlyUsageReport(
        from_,
        to,
        output_filename,
        Credentials(email=email, password=password, api_key=api_key),
        Optionals(host=host),
    ).run()
