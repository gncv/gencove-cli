"""Project import samples from S3 URI to projects shell command definition.
"""
import click

from gencove.command.common_cli_options import add_options, common_options
from gencove.constants import Credentials

from .constants import S3ImportOptionals
from .main import S3Import


@click.command("import")
@click.argument("s3_uri")
@click.argument("project_id")
@click.option(
    "--metadata-json",
    required=False,
    default=None,
    help=("Add metadata to all samples that are to be imported from S3 to a project."),
)
@add_options(common_options)
def s3_import(  # pylint: disable=too-many-arguments
    s3_uri,
    project_id,
    metadata_json,
    host,
    email,
    password,
    api_key,
):  # pylint: disable=line-too-long
    """Import all samples from a S3 URI to a project. Optionally add
    metadata to the samples.

    Examples:

        Import samples to a project:

            gencove s3 import s3://bucket/path/ 06a5d04b-526a-4471-83ba-fb54e0941758

        Import samples to a project:

            gencove s3 import s3://bucket/path/ 06a5d04b-526a-4471-83ba-fb54e0941758 --metadata-json='{"batch": "batch1"}'
    """  # noqa: E501
    S3Import(
        s3_uri,
        project_id,
        Credentials(email=email, password=password, api_key=api_key),
        S3ImportOptionals(host=host, metadata_json=metadata_json),
    ).run()
