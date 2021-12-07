"""Project autoimport from S3 URI shell command definition.
"""
import click

from gencove.command.common_cli_options import add_options, common_options
from gencove.constants import Credentials, Optionals

from .main import S3AutoImportList


@click.command("list")
@add_options(common_options)
def autoimport_list(
    host,
    email,
    password,
    api_key,
):
    """Lists S3 automatic import jobs.

    Examples:

        List S3 automatic import jobs:

            gencove s3 autoimports list
    """  # noqa: E501

    S3AutoImportList(
        Credentials(email=email, password=password, api_key=api_key),
        Optionals(host=host),
    ).run()
