"""Test instances inactivity-stop command."""
# pylint: disable=wrong-import-order, import-error
import io
import sys


from click import echo
from click.testing import CliRunner

from gencove.client import (
    APIClient,
    APIClientError,
)  # noqa: I100
from gencove.command.explorer.instances.cli import inactivity_stop
from gencove.models import (
    ExplorerInstance,
    ExplorerInstances,
)
from gencove.tests.decorators import assert_authorization
from gencove.tests.explorer.vcr.filters import (  # noqa: I101
    filter_list_instances_response,
    filter_instance_ids_request,
)
from gencove.tests.filters import filter_jwt, replace_gencove_url_vcr
from gencove.tests.upload.vcr.filters import filter_volatile_dates
from gencove.tests.utils import get_vcr_response

import pytest

from vcr import VCR


@pytest.fixture(scope="module")
def vcr_config():
    """VCR configuration."""
    return {
        "cassette_library_dir": "gencove/tests/explorer/vcr",
        "filter_headers": [
            "Authorization",
            "Content-Length",
            "User-Agent",
        ],
        "filter_post_data_parameters": [
            ("email", "email@example.com"),
            ("password", "mock_password"),
        ],
        "match_on": ["method", "scheme", "port", "path", "query"],
        "path_transformer": VCR.ensure_suffix(".yaml"),
        "before_record_request": [
            replace_gencove_url_vcr,
            filter_instance_ids_request,
        ],
        "before_record_response": [
            filter_jwt,
            filter_volatile_dates,
            filter_list_instances_response,
        ],
    }


@pytest.mark.default_cassette("jwt-create.yaml")
@pytest.mark.vcr
@assert_authorization
def test_inactivity_stop_no_permission(mocker, credentials):
    """Test instances no permission available to configure stop inactivity."""
    runner = CliRunner()
    mocked_get_instances = mocker.patch.object(
        APIClient,
        "get_explorer_instances",
        side_effect=APIClientError(
            message="API Client Error: Not Found: Not found.", status_code=403
        ),
        return_value={"detail": "Not found"},
    )
    res = runner.invoke(inactivity_stop, credentials)
    assert res.exit_code == 1
    mocked_get_instances.assert_called_once()

    output_line = io.BytesIO()
    sys.stdout = output_line
    echo(
        "\n".join(
            [
                "ERROR: You do not have the sufficient permission "
                "level required to perform this operation.",
                "ERROR: API Client Error: Not Found: Not found.",
                "Aborted!",
            ]
        )
    )
    assert output_line.getvalue() == res.output.encode()


@pytest.mark.vcr
@assert_authorization
def test_inactivity_stop(mocker, credentials, recording, vcr):
    """Test instances configured to stop after inactivity."""
    runner = CliRunner()
    if not recording:
        # Mock list_instances only if using the cassettes, since we mock the
        # return value.
        list_instances_response = get_vcr_response("/api/v2/explorer-instances/", vcr)
        mocked_get_instances = mocker.patch.object(
            APIClient,
            "get_explorer_instances",
            return_value=ExplorerInstances(**list_instances_response),
        )
    res = runner.invoke(inactivity_stop, ["--hours=3", *credentials])
    assert res.exit_code == 0
    if not recording:
        mocked_get_instances.assert_called_once()
        instances = list_instances_response["results"]
        output_line = io.BytesIO()
        sys.stdout = output_line
        echo("Inactivity stop configuration")
        for instance in instances:
            instance = ExplorerInstance(**instance)
            instance_id = str(instance.id).replace("-", "")
            echo(f"Instance {instance_id}:\thours=3")
        assert output_line.getvalue() == res.output.encode()


@pytest.mark.vcr
@assert_authorization
def test_inactivity_stop_organization(mocker, credentials, recording, vcr):
    """Test instances configured to stop after inactivity at organization level."""
    runner = CliRunner()
    if not recording:
        # Mock list_instances only if using the cassettes, since we mock the
        # return value.
        list_instances_response = get_vcr_response("/api/v2/explorer-instances/", vcr)
        mocked_get_instances = mocker.patch.object(
            APIClient,
            "get_explorer_instances",
            return_value=ExplorerInstances(**list_instances_response),
        )
    res = runner.invoke(inactivity_stop, ["--hours=3", "--organization", *credentials])
    assert res.exit_code == 0
    if not recording:
        mocked_get_instances.assert_called_once()
        output_line = io.BytesIO()
        sys.stdout = output_line
        echo("Inactivity stop configuration")
        echo("Organization:\t\t\t\t\thours=3, override=False")
        assert output_line.getvalue() == res.output.encode()


@pytest.mark.vcr
@assert_authorization
def test_inactivity_stop_organization_override(mocker, credentials, recording, vcr):
    """Test instances configured to stop after inactivity at
    organization level with override."""
    runner = CliRunner()
    if not recording:
        # Mock list_instances only if using the cassettes, since we mock the
        # return value.
        list_instances_response = get_vcr_response("/api/v2/explorer-instances/", vcr)
        mocked_get_instances = mocker.patch.object(
            APIClient,
            "get_explorer_instances",
            return_value=ExplorerInstances(**list_instances_response),
        )
    res = runner.invoke(
        inactivity_stop,
        ["--hours=3", "--organization", "--override=True", *credentials],
    )
    assert res.exit_code == 0
    if not recording:
        mocked_get_instances.assert_called_once()
        output_line = io.BytesIO()
        sys.stdout = output_line
        echo("Inactivity stop configuration")
        echo("Organization:\t\t\t\t\thours=3, override=True")
        assert output_line.getvalue() == res.output.encode()


@pytest.mark.vcr
@assert_authorization
def test_inactivity_stop_instance_override(mocker, credentials, recording, vcr):
    """Test instances stop inactivity config overwritten by org."""
    runner = CliRunner()
    if not recording:
        # Mock list_instances only if using the cassettes, since we mock the
        # return value.
        list_instances_response = get_vcr_response("/api/v2/explorer-instances/", vcr)
        mocked_get_instances = mocker.patch.object(
            APIClient,
            "get_explorer_instances",
            return_value=ExplorerInstances(**list_instances_response),
        )
    res = runner.invoke(inactivity_stop, ["--hours=None", *credentials])
    assert res.exit_code == 0
    if not recording:
        mocked_get_instances.assert_called_once()
        instances = list_instances_response["results"]
        output_line = io.BytesIO()
        sys.stdout = output_line
        echo("Inactivity stop configuration")
        for instance in instances:
            instance = ExplorerInstance(**instance)
            instance_id = str(instance.id).replace("-", "")
            echo(
                f"Instance {instance_id}:\thours=3 "
                "(applied from organization), "
                "instance_config[hours=None]"
            )
        assert output_line.getvalue() == res.output.encode()
