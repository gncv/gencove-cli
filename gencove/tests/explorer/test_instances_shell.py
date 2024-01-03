"""Test instances shell command."""
# pylint: disable=wrong-import-order, import-error
import io
import sys


from click import echo
from click.testing import CliRunner

from gencove.client import (
    APIClient,
    APIClientError,
)  # noqa: I100
from gencove.command.explorer.instances.cli import shell
from gencove.command.explorer.instances.shell.main import ShellSession
from gencove.tests.decorators import assert_authorization
from gencove.tests.explorer.vcr.filters import (  # noqa: I101
    filter_list_instances_response,
    filter_instance_ids_request,
    filter_session_credentials_response,
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
            filter_session_credentials_response,
        ],
    }


@pytest.mark.default_cassette("jwt-create.yaml")
@pytest.mark.vcr
@assert_authorization
def test_instances_shell_no_permission(mocker, credentials):
    """Test instances no permission available to shell them."""
    runner = CliRunner()
    mocker.patch(
        "gencove.command.explorer.instances.shell.main.user_has_aws_in_path",
        return_value=True,
    )
    mocker.patch(
        "gencove.command.explorer.instances.shell.main.user_has_supported_aws_cli",
        return_value=True,
    )
    mocker.patch(
        (
            "gencove.command.explorer.instances.shell.main."
            "user_has_session_manager_plugin_in_path"
        ),
        return_value=True,
    )
    mocked_get_instances = mocker.patch.object(
        APIClient,
        "get_explorer_instances",
        side_effect=APIClientError(
            message="API Client Error: Not Found: Not found.", status_code=403
        ),
        return_value={"detail": "Not found"},
    )
    res = runner.invoke(shell, credentials)
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
def test_instances_shell(mocker, credentials, recording, vcr):
    """Test instances shell."""
    runner = CliRunner()
    mocker.patch(
        "gencove.command.explorer.instances.shell.main.user_has_aws_in_path",
        return_value=True,
    )
    mocker.patch(
        "gencove.command.explorer.instances.shell.main.user_has_supported_aws_cli",
        return_value=True,
    )
    mocker.patch(
        (
            "gencove.command.explorer.instances.shell.main."
            "user_has_session_manager_plugin_in_path"
        ),
        return_value=True,
    )
    if not recording:
        # Mock shell only if using the cassettes, since we mock the
        # return value.
        get_vcr_response("/api/v2/explorer-shell-session-credentials/", vcr)
        mocked_instances_shell = mocker.patch.object(
            APIClient,
            "get_explorer_shell_session_credentials",
            return_value=None,
        )
    mocked_start_ssm_session = mocker.patch.object(
        ShellSession,
        "start_ssm_session",
    )
    res = runner.invoke(shell, credentials)
    assert res.exit_code == 0
    if not recording:
        mocked_instances_shell.assert_called_once()
    mocked_start_ssm_session.assert_called_once()
