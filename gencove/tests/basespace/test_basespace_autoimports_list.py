"""Test basespace autoimports list command."""

import os
import pytest

from click.testing import CliRunner

from gencove.client import APIClient, APIClientError, APIClientTimeout
from gencove.command.basespace.autoimports.autoimport_list.cli import (
    autoimport_list,
)
from gencove.models import (
    BaseSpaceProjectImport,
    BaseSpaceProjectImportDetail,
)
from gencove.tests.decorators import assert_authorization
from gencove.tests.filters import filter_jwt, replace_gencove_url_vcr
from gencove.tests.upload.vcr.filters import (
    filter_basespace_autoimport_list_response,
    filter_volatile_dates,
)
from gencove.tests.utils import get_vcr_response


from vcr import VCR


@pytest.fixture(scope="module")
def vcr_config():
    """VCR configuration."""
    return {
        "cassette_library_dir": "gencove/tests/basespace/vcr",
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
            filter_basespace_autoimport_list_response,
        ],
    }


@pytest.mark.vcr
@assert_authorization
def test_list_does_not_exist(mocker, credentials):
    """Test user cannot get to jobs."""
    runner = CliRunner()
    mocked_list_basespace_autoimport_jobs = mocker.patch.object(
        APIClient,
        "list_basespace_autoimport_jobs",
        side_effect=APIClientError(
            message="API Client Error: Not Found: Not found.", status_code=404
        ),
        return_value={"detail": "Not found"},
    )
    res = runner.invoke(autoimport_list, credentials)
    print(credentials)
    print(os.environ["GENCOVE_HOST"])
    assert isinstance(res.exception, SystemExit)
    assert res.exit_code == 1
    mocked_list_basespace_autoimport_jobs.assert_called_once()
    assert (
        "\n".join(
            [
                "ERROR: Uploads do not exist.",
                "ERROR: API Client Error: Not Found: Not found.",
                "Aborted!\n",
            ]
        )
        == res.output
    )
