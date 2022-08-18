"""Project assign all uploads from a prefix shell command definition."""
import click

from gencove.command.common_cli_options import add_options, common_options
from gencove.constants import Credentials, SampleAssignmentStatus
from gencove.utils import enum_as_dict


from .constants import RunPrefixOptionals
from .main import RunPrefix


@click.command("run-prefix")
@click.argument("project_id")
@click.argument("prefix")
@click.option(
    "--metadata-json",
    required=False,
    default=None,
    help=("Add metadata to all uploads that are to be assigned to a project."),
)
@click.option(
    "--status",
    help="Filter uploads by status of assignment",
    type=click.Choice(enum_as_dict(SampleAssignmentStatus).values()),
    default=SampleAssignmentStatus.ALL.value,
)
@add_options(common_options)
def run_prefix(  # pylint: disable=too-many-arguments
    project_id, prefix, metadata_json, status, host, email, password, api_key
):  # pylint: disable=C0301
    """Assign all uploads from Gencove prefix to a project. Optionally add
    metadata to the samples. Uploads can also be filtered through status.

    Examples:

        Assign uploads to a project:

            gencove projects run-prefix 06a5d04b-526a-4471-83ba-fb54e0941758 gncv://my-project/path

        Assign uploads to a project with metadata:

            gencove projects run-prefix 06a5d04b-526a-4471-83ba-fb54e0941758 gncv://my-project/path --metadata-json='{"batch": "batch1"}'

        Assign uploads filtered by status to a project:

            gencove projects run-prefix 06a5d04b-526a-4471-83ba-fb54e0941758 gncv://my-project/path --status assigned
    """  # noqa: E501
    RunPrefix(
        project_id,
        prefix,
        Credentials(email=email, password=password, api_key=api_key),
        RunPrefixOptionals(host=host, metadata_json=metadata_json, status=status),
    ).run()
