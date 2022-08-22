"""Project import Biosamples from BaseSpace projects shell command definition.
"""
import click

from gencove.command.common_cli_options import add_options, common_options
from gencove.constants import Credentials
from gencove.logger import echo_debug

from .constants import BaseSpaceImportOptionals
from .main import BaseSpaceImport


@click.command("import")
@click.argument("basespace_project_ids")
@click.argument("project_id")
@click.option(
    "--metadata-json",
    required=False,
    default=None,
    help=(
        "Add metadata to all samples that are to be imported from "
        "BaseSpace to a project."
    ),
)
@add_options(common_options)
def basespace_import(  # pylint: disable=too-many-arguments
    basespace_project_ids,
    project_id,
    metadata_json,
    host,
    email,
    password,
    api_key,
):  # pylint: disable=line-too-long
    """Import all Biosamples from BaseSpace projects to a project. Optionally add
    metadata to the samples.

    Examples:

        Import Biosamples to a project:

            gencove basespace projects import 12345678 06a5d04b-526a-4471-83ba-fb54e0941758

        Import Biosamples from multiple BaseSpace projects to a project:

            gencove basespace projects import 12345678,87654321 06a5d04b-526a-4471-83ba-fb54e0941758

        Import Biosamples to a project with metadata:

            gencove basespace projects import 12345678 06a5d04b-526a-4471-83ba-fb54e0941758 --metadata-json='{"batch": "batch1"}'
    """  # noqa: E501
    basespace_project_ids = [
        basespace_project_id.strip()
        for basespace_project_id in basespace_project_ids.split(",")
    ]
    echo_debug(f"BaseSpace project ids translation: {basespace_project_ids}")

    BaseSpaceImport(
        basespace_project_ids,
        project_id,
        Credentials(email=email, password=password, api_key=api_key),
        BaseSpaceImportOptionals(host=host, metadata_json=metadata_json),
    ).run()
