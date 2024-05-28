"""Configure presign for explorer data command definition.
"""
import click

from gencove.command.common_cli_options import add_options, common_options
from gencove.constants import Credentials, Optionals

from .main import Presign


@click.command(
    "presign",
    help="Generate a presigned URL for an object in Explorer object storage",
    context_settings=dict(
        ignore_unknown_options=True,
        allow_extra_args=True,
    ),
)
@click.argument("path", type=click.Path())
@click.pass_context
@add_options(common_options)
def presign(  # pylint: disable=too-many-arguments,invalid-name
    ctx,
    path,
    host,
    email,
    password,
    api_key,
):  # pylint: disable=line-too-long
    """Start instances."""  # noqa: E501
    Presign(
        ctx,
        path,
        Credentials(email=email, password=password, api_key=api_key),
        Optionals(host=host),
    ).run()
