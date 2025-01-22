"""Test data cp command."""
import io
import os
import sys
import uuid
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
from gencove.command.explorer.data.cp.main import Copy
from gencove.constants import Credentials, HOST, Optionals
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
    assert res.exit_code == 0

    if not recording:
        mocked_get_credentials.assert_called_once()
        mocked_aws.assert_called_once()
    else:
        assert "test_cp.txt" in res.output


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


def test_data_read_credentials_from_env(mocker, credentials):
    """
    Make sure credentials are from env variables on explorer.
    This test fails when a request to the API is made.
    Is heavily mocked in API interaction and validation to make sure we don't
    do any unnecessary requests.
    """

    mocked_request_is_from_explorer = mocker.patch(
        "gencove.command.explorer.data.cp.main.request_is_from_explorer",
        return_value=True,
    )
    mock_user_id = uuid.uuid4().hex
    mock_org_id = uuid.uuid4().hex
    os.environ["GENCOVE_USER_ID"] = mock_user_id
    os.environ["GENCOVE_ORGANIZATION_ID"] = mock_org_id

    # Setup credentials dataclass
    if "--email" in credentials:
        credentials = Credentials(
            email=credentials[1], password=credentials[3], api_key=""
        )
    else:
        credentials = Credentials(email="", password="", api_key=credentials[0])

    # Setup "Copy" object
    _copy = Copy(
        {},
        "e://users/me/file-a.txt",
        "e://users/me/file-b.txt",
        credentials,
        Optionals(host=HOST),
    )
    setattr(_copy, "login", lambda: None)
    setattr(_copy, "validate_login_success", lambda: None)
    setattr(_copy, "execute", lambda: None)

    # Should read explorer credentials from env
    _copy.initialize()

    # Make sure the Copy object was correctly setup
    mocked_request_is_from_explorer.assert_called()
    assert str(_copy.user_id).replace("-", "") == mock_user_id
    assert str(_copy.organization_id).replace("-", "") == mock_org_id
    assert _copy.explorer_enabled
    assert not _copy.aws_session_credentials
