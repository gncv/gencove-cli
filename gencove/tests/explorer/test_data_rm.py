"""Test data rm command."""
import io
import os
import sys
import uuid

# pylint: disable=wrong-import-order, import-error

from click import echo
from click.testing import CliRunner

from gencove.client import (
    APIClient,
    APIClientError,
)  # noqa: I100
from gencove.command.explorer.data.cli import rm
from gencove.command.explorer.data.common import GencoveExplorerManager
from gencove.models import AWSCredentials
from gencove.tests.decorators import assert_authorization
from gencove.tests.explorer.vcr.filters import (  # noqa: I101
    filter_data_credentials_response,
)
from gencove.tests.filters import filter_jwt, replace_gencove_url_vcr
from gencove.tests.upload.vcr.filters import filter_volatile_dates
from gencove.tests.utils import get_vcr_response
from gencove.command.explorer.data.rm.main import Remove
from gencove.constants import Credentials, Optionals, HOST

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
def test_data_rm_success(mocker, credentials, recording, vcr):
    """Test data being output to shell."""
    runner = CliRunner()
    mocker.patch(
        "gencove.command.explorer.data.rm.main.user_has_aws_in_path", return_value=True
    )
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

    # Assumption that CLI user has a file called rm_test_file.txt in their
    # Explorer files dir. If the cassette must be regenerated, upload a test file to
    # "e://users/me/rm_test_file.txt"
    res = runner.invoke(rm, ["e://users/me/rm_test_file.txt", *credentials])

    if not recording:
        mocked_get_credentials.assert_called_once()
        mocked_aws.assert_called_once()
    else:
        assert "rm_test_file.txt" in res.output

    assert res.exit_code == 0


@pytest.mark.vcr
@assert_authorization
def test_data_rm_no_permission(mocker, credentials):
    """Test no permissions for credentials endpoint."""
    runner = CliRunner()
    mocker.patch(
        "gencove.command.explorer.data.rm.main.user_has_aws_in_path", return_value=True
    )
    mocked_get_credentials = mocker.patch.object(
        APIClient,
        "get_explorer_data_credentials",
        side_effect=APIClientError(
            message="API Client Error: Not Found: Not found.", status_code=403
        ),
        return_value={"detail": "Not found"},
    )

    res = runner.invoke(rm, ["e://users/me/rm_test_file.txt", *credentials])

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
        "gencove.command.explorer.data.ls.main.request_is_from_explorer",
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

    # Setup "Remove" object
    rm = Remove(
        {},
        "e://users/me/",
        credentials,
        Optionals(host=HOST),
    )
    setattr(rm, "login", lambda: None)
    setattr(rm, "validate_login_success", lambda: None)
    setattr(rm, "execute", lambda: None)

    # Should read explorer credentials from env
    rm.initialize()

    # Make sure the Remove object was correctly setup
    mocked_request_is_from_explorer.assert_called()
    assert str(rm.user_id).replace("-", "") == mock_user_id
    assert str(rm.organization_id).replace("-", "") == mock_org_id
    assert rm.explorer_enabled
    assert not rm.aws_session_credentials
