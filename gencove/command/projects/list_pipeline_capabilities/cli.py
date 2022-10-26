"""Pipeline capabilities list shell command definition."""
import click

from gencove.command.common_cli_options import add_options, common_options
from gencove.command.utils import validate_uuid
from gencove.constants import Credentials, Optionals

from .main import ListPipelineCapabilities


@click.command("list-pipeline-capabilities")
@click.argument("pipeline_id", callback=validate_uuid)
@add_options(common_options)
def list_project_pipeline_capabilities(pipeline_id, host, email, password, api_key):
    """List pipeline capabilities that are available for a pipeline."""
    ListPipelineCapabilities(
        pipeline_id,
        Credentials(email=email, password=password, api_key=api_key),
        Optionals(host=host),
    ).run()
