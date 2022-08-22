"""Project autoimport from S3 shell command definition.
"""
import click

from gencove.command.common_cli_options import add_options, common_options
from gencove.constants import Credentials

from .constants import S3AutoImportOptionals
from .main import S3AutoImport


@click.command("create")
@click.argument("project_id")
@click.argument("s3_uri")
@click.option(
    "--metadata-json",
    required=False,
    default=None,
    help=("Add metadata to all samples that are to be imported from S3 to a project."),
)
@add_options(common_options)
def create(  # pylint: disable=too-many-arguments
    project_id,
    s3_uri,
    metadata_json,
    host,
    email,
    password,
    api_key,
):  # pylint: disable=line-too-long
    """Sets up automatic import from S3 URI to a project in Gencove. Optionally assign metadata to the samples to be added when the automatic
    import job runs.

    Examples:

        Set up automatic import from S3 to a project:

            gencove s3 autoimports create 06a5d04b-526a-4471-83ba-fb54e0941758 s3://bucket/path/to/project

        Set up automatic import from S3 to a project with metadata:

            gencove s3 autoimports create 06a5d04b-526a-4471-83ba-fb54e0941758 s3://bucket/path/to/project --metadata-json='{"batch": "batch1"}'
    """  # noqa: E501

    S3AutoImport(
        project_id,
        s3_uri,
        Credentials(email=email, password=password, api_key=api_key),
        S3AutoImportOptionals(host=host, metadata_json=metadata_json),
    ).run()
