"""Test data cp command."""
import io
import sys
from pathlib import Path

# pylint: disable=wrong-import-order, import-error

from click import echo
from click.testing import CliRunner

from gencove.client import (
    APIClient,
    APIClientError,
)  # noqa: I100
from gencove.command.explorer.data.cli import cp
from gencove.command.explorer.data.common import GencoveExplorerManager
from gencove.models import ExplorerDataCredentials
from gencove.tests.decorators import assert_authorization
from gencove.tests.explorer.vcr.filters import (  # noqa: I101
    filter_data_credentials_response,
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
        ],
        "before_record_response": [
            filter_jwt,
            filter_volatile_dates,
            filter_data_credentials_response,
        ],
    }


@pytest.mark.vcr
@assert_authorization
def test_data_cp_success(mocker, credentials, recording, vcr):
    """Test data being output to shell."""
    runner = CliRunner()
    mocker.patch(
        "gencove.command.explorer.data.cp.main.user_has_aws_in_path", return_value=True
    )
    if not recording:
        credentials_response = get_vcr_response(
            "/api/v2/explorer-data-credentials/", vcr
        )
        mocked_get_credentials = mocker.patch.object(
            APIClient,
            "get_explorer_data_credentials",
            return_value=ExplorerDataCredentials(**credentials_response),
        )
        mocked_aws = mocker.patch.object(
            GencoveExplorerManager, "execute_aws_s3_src_dst", return_value=None
        )

    test_file = Path(__file__).parent / "test_cp.txt"
    res = runner.invoke(cp, [str(test_file), "e://users/me/test_cp.txt", *credentials])

    if not recording:
        mocked_get_credentials.assert_called_once()
        mocked_aws.assert_called_once()
    else:
        assert "test_cp.txt" in res.output

    assert res.exit_code == 0


@pytest.mark.vcr
@assert_authorization
def test_data_cp_no_permission(mocker, credentials):
    """Test no permissions for credentials endpoint."""
    runner = CliRunner()
    mocker.patch(
        "gencove.command.explorer.data.cp.main.user_has_aws_in_path", return_value=True
    )
    mocked_get_credentials = mocker.patch.object(
        APIClient,
        "get_explorer_data_credentials",
        side_effect=APIClientError(
            message="API Client Error: Not Found: Not found.", status_code=403
        ),
        return_value={"detail": "Not found"},
    )

    test_file = Path(__file__).parent / "test_cp.txt"
    res = runner.invoke(cp, [str(test_file), "e://users/me/test_cp.txt", *credentials])
    assert res.exit_code == 1

    mocked_get_credentials.assert_called_once()

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
