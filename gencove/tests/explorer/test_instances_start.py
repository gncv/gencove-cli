"""Test instances start command."""
# pylint: disable=wrong-import-order, import-error
import io
import sys


from click import echo
from click.testing import CliRunner

from gencove.client import (
    APIClient,
    APIClientError,
)  # noqa: I100
from gencove.command.explorer.instances.cli import start
from gencove.models import (
    ExplorerInstance,
    ExplorerInstances,
    ResponseMeta,
)
from gencove.tests.decorators import assert_authorization
from gencove.tests.explorer.vcr.filters import (  # noqa: I101
    filter_list_instances_response,
    filter_instance_ids_request,
)
from gencove.tests.filters import filter_jwt, replace_gencove_url_vcr
from gencove.tests.upload.vcr.filters import filter_volatile_dates
from gencove.tests.utils import MOCK_UUID, get_vcr_response

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
def test_instances_start_no_permission(mocker, credentials):
    """Test instances no permission available to start them."""
    runner = CliRunner()
    mocked_get_instances = mocker.patch.object(
        APIClient,
        "get_explorer_instances",
        side_effect=APIClientError(
            message="API Client Error: Not Found: Not found.", status_code=403
        ),
        return_value={"detail": "Not found"},
    )
    res = runner.invoke(start, credentials)
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
def test_instances_start(mocker, credentials, recording, vcr):
    """Test instances started."""
    runner = CliRunner()
    if not recording:
        # Mock start only if using the cassettes, since we mock the
        # return value.
        get_vcr_response("/api/v2/explorer-start-instances/", vcr)
        mocked_instances_start = mocker.patch.object(
            APIClient,
            "start_explorer_instances",
            return_value=None,
        )
    res = runner.invoke(start, credentials)
    assert b"Request to start explorer instances accepted." in res.output.encode()
    assert res.exit_code == 0
    if not recording:
        mocked_instances_start.assert_called_once()


@pytest.mark.vcr
@assert_authorization
def test_instances_start_not_stopped(mocker, credentials, recording, vcr):
    """Test instances not being stopped."""
    runner = CliRunner()
    if not recording:
        # Mock start only if using the cassettes, since we mock the
        # return value.
        response_json = get_vcr_response("/api/v2/explorer-start-instances/", vcr)
        error_msg = "\n".join(
            [
                f"  {key}: {value[0] if isinstance(value, list) else str(value)}"  # noqa: E501  # pylint: disable=line-too-long
                for key, value in response_json.items()
            ]
        )
        mocked_instances_start = mocker.patch.object(
            APIClient,
            "start_explorer_instances",
            side_effect=APIClientError(
                message=f"API Client Error: Bad Request:\n{error_msg}",
                status_code=400,
            ),
        )
    res = runner.invoke(start, credentials)
    assert b"not in stopped status" in res.output.encode()
    assert res.exit_code == 1
    if not recording:
        mocked_instances_start.assert_called_once()


@pytest.mark.vcr
@pytest.mark.default_cassette("jwt-create.yaml")
@assert_authorization
def test_instances_start_update_cli(mocker, credentials):
    """Test instances being not stopped because CLI is outdated."""
    runner = CliRunner()
    mocked_get_instances = mocker.patch.object(
        APIClient,
        "get_explorer_instances",
        return_value=ExplorerInstances(
            meta=ResponseMeta(count=2, next=None, previous=None),
            results=[
                ExplorerInstance(
                    id=MOCK_UUID, status="running", stop_after_inactivity_hours=None
                ),
                ExplorerInstance(
                    id=MOCK_UUID, status="running", stop_after_inactivity_hours=None
                ),
            ],
        ),
    )
    res = runner.invoke(start, credentials)
    assert (
        b"Command not supported. Download the latest version of the Gencove CLI."
        in res.output.encode()
    )
    assert res.exit_code == 1
    mocked_get_instances.assert_called_once()
