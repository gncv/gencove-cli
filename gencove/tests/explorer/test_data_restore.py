"""Test data restore command."""
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
from gencove.command.explorer.data.cli import restore
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
def test_data_restore_success(mocker, credentials, recording, vcr):
    """Test data being output to shell."""
    runner = CliRunner()
    mocker.patch(
        "gencove.command.explorer.data.restore.main.user_has_aws_in_path",
        return_value=True,
    )
    mocked_thread_safe_client = mocker.patch.object(
        GencoveExplorerManager, "thread_safe_client"
    )
    objects_in_storage = [
        {
            "Key": f"example{i}.fastq.gz",
            "StorageClass": "DEEP_ARCHIVE" if i % 2 == 0 else "STANDARD",
        }
        for i in range(100)
    ]
    mocked_list_objects = mocker.patch.object(
        GencoveExplorerManager,
        "list_s3_objects",
        return_value=[{"Contents": objects_in_storage}],
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

    restore_path = "e://users/me/"
    res = runner.invoke(restore, [restore_path, *credentials])
    assert res.exit_code == 0

    if not recording:
        mocked_get_credentials.assert_called_once()
    mocked_thread_safe_client.assert_called_with("s3")
    mocked_list_objects.assert_called_with(restore_path)
    assert (
        mocked_thread_safe_client.return_value.restore_object.call_count
        == len(objects_in_storage) // 2
    )


@pytest.mark.vcr
@assert_authorization
def test_data_restore_no_permission(mocker, credentials):
    """Test no permissions for credentials endpoint."""
    runner = CliRunner()
    mocker.patch(
        "gencove.command.explorer.data.restore.main.user_has_aws_in_path",
        return_value=True,
    )
    mocked_get_credentials = mocker.patch.object(
        APIClient,
        "get_explorer_data_credentials",
        side_effect=APIClientError(
            message="API Client Error: Not Found: Not found.", status_code=403
        ),
        return_value={"detail": "Not found"},
    )

    res = runner.invoke(restore, ["e://users/me/", *credentials])

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
    """Test read credentials from env on explorer."""
    runner = CliRunner()
    mocked_request_is_from_explorer = mocker.patch(
        "gencove.command.explorer.data.restore.main.request_is_from_explorer",
        return_value=True,
    )
    mocker.patch("gencove.command.explorer.data.restore.main.Restore.execute")
    os.environ["GENCOVE_USER_ID"] = uuid.uuid4().hex
    os.environ["GENCOVE_ORGANIZATION_ID"] = uuid.uuid4().hex

    runner.invoke(restore, ["e://users/me/", *credentials])

    mocked_request_is_from_explorer.assert_called()
