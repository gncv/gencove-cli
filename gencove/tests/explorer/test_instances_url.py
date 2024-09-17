"""Test instances url command."""
# pylint: disable=wrong-import-order, import-error
import io
import sys

from click import echo
from click.testing import CliRunner

from gencove.client import (
    APIClient,
    APIClientError,
)  # noqa: I100
from gencove.command.explorer.instances.cli import url
from gencove.models import (
    ExplorerAccessURL,
    ExplorerInstance,
    ExplorerInstances,
    ResponseMeta,
)
from gencove.tests.decorators import assert_authorization
from gencove.tests.explorer.vcr.filters import (  # noqa: I101
    filter_explorer_access_url_response,
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
            filter_explorer_access_url_response,
            filter_list_instances_response,
        ],
    }


@pytest.mark.default_cassette("jwt-create.yaml")
@pytest.mark.vcr
@assert_authorization
def test_instances_url_no_permission(mocker, credentials):
    """Test instances no permission available to access URL."""
    runner = CliRunner()
    mocked_get_instances = mocker.patch.object(
        APIClient,
        "get_explorer_instances",
        side_effect=APIClientError(
            message="API Client Error: Not Found: Not found.", status_code=403
        ),
        return_value={"detail": "Not found"},
    )
    res = runner.invoke(url, credentials)
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
def test_instances_url(mocker, credentials, recording, vcr):
    """Test instances url."""
    runner = CliRunner()
    if not recording:
        # Mock url only if using the cassettes, since we mock the
        # return value.
        get_vcr_response("/api/v2/explorer-access-url/", vcr)
        mocked_instances_url = mocker.patch.object(
            APIClient,
            "get_explorer_access_url",
            return_value=ExplorerAccessURL(
                url="https://mock-url.com/gncv-explorer/signin?access_token=123"
            ),
        )
    res = runner.invoke(url, credentials)
    assert b"Request to generate explorer access URL accepted." in res.output.encode()
    assert res.exit_code == 0
    if not recording:
        mocked_instances_url.assert_called_once()


@pytest.mark.vcr
@assert_authorization
def test_instances_url_with_expiration(mocker, credentials, recording, vcr):
    """Test instances url with custom expiration."""
    runner = CliRunner()
    if not recording:
        # Mock url only if using the cassettes, since we mock the
        # return value.
        get_vcr_response("/api/v2/explorer-access-url/", vcr)
        mocked_instances_url = mocker.patch.object(
            APIClient,
            "get_explorer_access_url",
            return_value=ExplorerAccessURL(
                url="https://mock-url.com/gncv-explorer/signin?access_token=123",
                access_token_expiration=3600,
            ),
        )

    # Add expiration seconds parameter
    res = runner.invoke(url, credentials + ["--expiration-seconds", 3600])
    assert b"Request to generate explorer access URL accepted." in res.output.encode()
    assert res.exit_code == 0
    if not recording:
        mocked_instances_url.assert_called_once()


@pytest.mark.vcr
@pytest.mark.default_cassette("jwt-create.yaml")
@assert_authorization
def test_instances_url_update_cli(mocker, credentials):
    """Test instances url not generated because CLI is outdated."""
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
    res = runner.invoke(url, credentials)
    assert (
        b"Command not supported. Download the latest version of the Gencove CLI."
        in res.output.encode()
    )
    assert res.exit_code == 1
    mocked_get_instances.assert_called_once()


@pytest.mark.vcr
@assert_authorization
def test_instances_url_with_invalid_expiration(mocker, credentials, recording, vcr):
    """Test instances url with invalid expiration."""
    runner = CliRunner()
    if not recording:
        # Mock url only if using the cassettes, since we mock the
        # return value.
        access_url_response = get_vcr_response("/api/v2/explorer-access-url/", vcr)
        mocked_instances_url = mocker.patch.object(
            APIClient,
            "get_explorer_access_url",
            side_effect=APIClientError(
                message=access_url_response["access_token_expiration"], status_code=400
            ),
        )

    # Add invalid expiration seconds parameter
    res = runner.invoke(url, credentials + ["--expiration-seconds", 1000000])
    assert b"Request to generate explorer access URL accepted." in res.output.encode()
    assert res.exit_code == 1
    assert "Ensure this value is less than" in res.output
    if not recording:
        mocked_instances_url.assert_called_once()
