"""Project autoimport Biosamples from BaseSpace projects shell command
definition.
"""
import click

from gencove.command.common_cli_options import add_options, common_options
from gencove.constants import Credentials

from .constants import BaseSpaceAutoImportOptionals
from .main import BaseSpaceAutoImport


@click.command("create")
@click.argument("project_id")
@click.argument("identifier")
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
def create(  # pylint: disable=too-many-arguments
    project_id,
    identifier,
    metadata_json,
    host,
    email,
    password,
    api_key,
):  # pylint: disable=line-too-long
    """Sets up periodic import of BaseSpace projects (their Biosamples) whose name contain the identifer
    to a project in Gencove. Optionally assign metadata to the samples to be added when the automatic
    import job runs.

    Examples:

        Set up automatic import of BaseSpace projects' samples that contain the identifier to a project:

            gencove basespace autoimports create 06a5d04b-526a-4471-83ba-fb54e0941758 identifier-in-basespace-project-name

        Set up automatic import of BaseSpace projects' samples that contain the identifier to a project with metadata:

            gencove basespace autoimports create 06a5d04b-526a-4471-83ba-fb54e0941758 identifier-in-basespace-project-name --metadata-json='{"batch": "batch1"}'
    """  # noqa: E501

    BaseSpaceAutoImport(
        project_id,
        identifier,
        Credentials(email=email, password=password, api_key=api_key),
        BaseSpaceAutoImportOptionals(host=host, metadata_json=metadata_json),
    ).run()
