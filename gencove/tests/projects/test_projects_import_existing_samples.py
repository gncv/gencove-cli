"""Test import existing project samples command."""

# pylint: disable=wrong-import-order, import-error
import operator
from uuid import uuid4

from click.testing import CliRunner

from gencove.client import APIClient, APIClientError
from gencove.command.projects.cli import import_existing_project_samples
from gencove.models import ImportExistingSamplesModel
from gencove.tests.decorators import assert_authorization
from gencove.tests.filters import filter_jwt, replace_gencove_url_vcr
from gencove.tests.projects.vcr.filters import (
    filter_import_existing_samples_request,
    filter_import_existing_samples_response,
)
from gencove.tests.utils import MOCK_UUID, get_vcr_response

import pytest

from vcr import VCR


@pytest.fixture(scope="module")
def vcr_config():
    """VCR configuration."""
    return {
        "cassette_library_dir": "gencove/tests/projects/vcr",
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
            filter_import_existing_samples_request,
        ],
        "before_record_response": [
            filter_jwt,
            filter_import_existing_samples_response,
        ],
    }


def test_import_existing_project_samples__bad_project_id(mocker):
    """Test import existing project samples failure when non-uuid string is used as
    project id.
    """
    runner = CliRunner()

    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_import_existing_samples = mocker.patch.object(
        APIClient,
        "import_existing_samples",
    )

    res = runner.invoke(
        import_existing_project_samples,
        [
            "1111111",
            "--email",
            "foo@bar.com",
            "--password",
            "123",
            "--samples",
            '[{"sample_id": "somevalue"}]',
        ],
    )

    assert res.exit_code == 1
    mocked_login.assert_called_once()
    mocked_import_existing_samples.assert_not_called()
    assert "Project ID is not valid" in res.output


def test_import_existing_project_samples__bad_samples_json(mocker):
    """Test import existing project samples failure when samples
    is a bad JSON.
    """
    runner = CliRunner()

    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_import_existing_samples = mocker.patch.object(
        APIClient,
        "import_existing_samples",
    )

    res = runner.invoke(
        import_existing_project_samples,
        [
            str(uuid4()),
            "--email",
            "foo@bar.com",
            "--password",
            "123",
            "--samples",
            '[{"sample_id": "somevalue"}',
        ],
    )

    assert res.exit_code == 1
    mocked_login.assert_called_once()
    mocked_import_existing_samples.assert_not_called()
    assert "Samples JSON is not valid" in res.output


def test_import_existing_project_samples__bad_samples_content_not_list(
    mocker,
):
    """Test import existing project samples failure when samples JSON
    is not a list.
    """
    runner = CliRunner()

    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_import_existing_samples = mocker.patch.object(
        APIClient,
        "import_existing_samples",
    )

    res = runner.invoke(
        import_existing_project_samples,
        [
            str(uuid4()),
            "--email",
            "foo@bar.com",
            "--password",
            "123",
            "--samples",
            '{"sample_id": "somevalue"}',
        ],
    )

    assert res.exit_code == 1
    mocked_login.assert_called_once()
    mocked_import_existing_samples.assert_not_called()
    assert "The samples JSON must be a JSON array of objects" in res.output


def test_import_existing_project_samples__bad_samples_content_not_dict_item(
    mocker,
):
    """Test import existing project samples failure when samples JSON
    is not a list of dicts.
    """
    runner = CliRunner()

    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_import_existing_samples = mocker.patch.object(
        APIClient,
        "import_existing_samples",
    )

    res = runner.invoke(
        import_existing_project_samples,
        [
            str(uuid4()),
            "--email",
            "foo@bar.com",
            "--password",
            "123",
            "--samples",
            "[1]",
        ],
    )

    assert res.exit_code == 1
    mocked_login.assert_called_once()
    mocked_import_existing_samples.assert_not_called()
    assert "The samples JSON must be a JSON array of objects" in res.output


def test_import_existing_project_samples__bad_samples_content_no_key_in_dict_item(  # noqa: E501  # pylint: disable=line-too-long
    mocker,
):
    """Test import existing project samples failure when samples JSON
    dict item in a list doesn't have the sample_id key.
    """
    runner = CliRunner()

    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_import_existing_samples = mocker.patch.object(
        APIClient,
        "import_existing_samples",
    )

    res = runner.invoke(
        import_existing_project_samples,
        [
            str(uuid4()),
            "--email",
            "foo@bar.com",
            "--password",
            "123",
            "--samples",
            '[{"foo": "somevalue"}]',
        ],
    )

    assert res.exit_code == 1
    mocked_login.assert_called_once()
    mocked_import_existing_samples.assert_not_called()
    assert "The samples JSON must be a JSON array of objects" in res.output


def test_import_existing_project_samples__bad_samples_bad_key_value_in_dict_item(  # noqa: E501  # pylint: disable=line-too-long
    mocker,
):
    """Test import existing project samples failure when samples JSON
    dict item in a list has the sample_id key with a bad value.
    """
    runner = CliRunner()

    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_import_existing_samples = mocker.patch.object(
        APIClient,
        "import_existing_samples",
    )

    res = runner.invoke(
        import_existing_project_samples,
        [
            str(uuid4()),
            "--email",
            "foo@bar.com",
            "--password",
            "123",
            "--samples",
            '[{"sample_id": "somevalue"}]',
        ],
    )

    assert res.exit_code == 1
    mocked_login.assert_called_once()
    mocked_import_existing_samples.assert_not_called()
    assert (
        "Sample ID {} is not a valid UUID. Exiting.".format("somevalue")
        in res.output
    )


def test_import_existing_project_samples__bad_samples_bad_optional_key_value_in_dict_item(  # noqa: E501  # pylint: disable=line-too-long
    mocker,
):
    """Test import existing project samples failure when samples JSON dict item
    in a list has the optional client_id key with a bad value.
    """
    runner = CliRunner()

    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_import_existing_samples = mocker.patch.object(
        APIClient,
        "import_existing_samples",
    )

    bad_sample_id = str(uuid4())
    bad_client_id = "foo_bar"
    res = runner.invoke(
        import_existing_project_samples,
        [
            str(uuid4()),
            "--email",
            "foo@bar.com",
            "--password",
            "123",
            "--samples",
            '[{"sample_id": "'
            + bad_sample_id
            + '", "client_id": "'
            + bad_client_id
            + '"}]',
        ],
    )

    assert res.exit_code == 1
    mocked_login.assert_called_once()
    mocked_import_existing_samples.assert_not_called()
    assert (
        "Client ID: {} for the sample {} is not valid. "
        "It cannot contain an underscore. Exiting.".format(
            bad_client_id, bad_sample_id
        )
        in res.output
    )


def test_import_existing_project_samples__bad_metadata(mocker):
    """Test import existing project samples failure when optional
    metadata-json is passed, but it has a bad value.
    """
    runner = CliRunner()

    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_import_existing_samples = mocker.patch.object(
        APIClient,
        "import_existing_samples",
    )

    res = runner.invoke(
        import_existing_project_samples,
        [
            str(uuid4()),
            "--email",
            "foo@bar.com",
            "--password",
            "123",
            "--samples",
            '[{"sample_id": "' + str(uuid4()) + '"}]',
            "--metadata-json",
            '[{"foo": "bar"}',
        ],
    )

    assert res.exit_code == 1
    mocked_login.assert_called_once()
    mocked_import_existing_samples.assert_not_called()
    assert "Metadata JSON is not valid" in res.output


@pytest.mark.vcr
@assert_authorization
def test_import_existing_project_samples__server_rejects(
    mocker, credentials, project_id, recording, vcr
):
    """Test import existing project samples failure when the validation
    fails on server.
    """
    runner = CliRunner()

    if not recording:
        # Mock import_existing_samples only if using the cassettes, since we
        # mock the return value.
        project_samples_import_response = get_vcr_response(
            "/api/v2/project-samples-import/",
            vcr,
            operator.contains,
            just_body=False,
        )
        mocked_import_existing_samples = mocker.patch.object(
            APIClient,
            "import_existing_samples",
            side_effect=APIClientError(
                message=project_samples_import_response["body"]["string"],
                status_code=project_samples_import_response["status"]["code"],
            ),
        )

    res = runner.invoke(
        import_existing_project_samples,
        [
            project_id,
            "--samples",
            '[{"sample_id": "' + MOCK_UUID + '"}]',
            *credentials,
        ],
    )
    assert res.exit_code == 1
    if not recording:
        mocked_import_existing_samples.assert_called_once()
    assert "There was an error importing" in res.output


@pytest.mark.vcr
@assert_authorization
def test_import_existing_project_samples__success(
    mocker, credentials, project_id, sample_id_import_existing, recording, vcr
):  # pylint: disable=too-many-arguments
    """Test import existing project samples success."""
    runner = CliRunner()

    if not recording:
        # Mock import_existing_samples only if using the cassettes, since we
        # mock the return value.
        project_samples_import_response = get_vcr_response(
            "/api/v2/project-samples-import/", vcr, operator.contains
        )
        mocked_import_existing_samples = mocker.patch.object(
            APIClient,
            "import_existing_samples",
            return_value=ImportExistingSamplesModel(
                **project_samples_import_response
            ),
        )

    res = runner.invoke(
        import_existing_project_samples,
        [
            project_id,
            "--samples",
            '[{"sample_id": "' + sample_id_import_existing + '"}]',
            *credentials,
        ],
    )
    assert res.exit_code == 0
    if not recording:
        mocked_import_existing_samples.assert_called_once()
    assert "Number of samples imported into the project" in res.output
