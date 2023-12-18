"""Test data ls command."""

# pylint: disable=wrong-import-order, import-error

from click.testing import CliRunner

from gencove.client import (
    APIClient,
)  # noqa: I100
from gencove.command.explorer.data.cli import ls
from gencove.command.explorer.data.common import GencoveExplorerManager
from gencove.models import AWSCredentials
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
def test_data_ls_success(mocker, credentials, recording, vcr):
    """Test data being output to shell."""
    runner = CliRunner()
    if not recording:
        credentials_response = get_vcr_response(
            "/api/v2/explorer-data-credentials/", vcr
        )
        mocked_get_credentials = mocker.patch.object(
            APIClient,
            "get_explorer_data_credentials",
            return_value=AWSCredentials(**credentials_response),
        )
        mocked_aws = mocker.patch.object(
            GencoveExplorerManager, "execute_aws_s3_path", return_value=None
        )

    res = runner.invoke(ls, ["e://users/me/", *credentials])

    if not recording:
        mocked_get_credentials.assert_called_once()
        mocked_aws.assert_called_once()
    else:
        assert "cli_test_file.txt" in res.output

    assert res.exit_code == 0
