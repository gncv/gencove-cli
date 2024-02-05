"""Test file types list command"""
# pylint: disable=wrong-import-order, import-error
import operator
from uuid import uuid4

from click.testing import CliRunner

from gencove.client import APIClient, APIClientError
from gencove.command.files.cli import list_file_types
from gencove.models import FileTypesModel
from gencove.tests.decorators import assert_authorization
from gencove.tests.filters import filter_file_types_request
from gencove.tests.filters import filter_jwt, replace_gencove_url_vcr
from gencove.tests.utils import get_vcr_response

import pytest

from vcr import VCR


@pytest.fixture(scope="module")
def vcr_config():
    """VCR configuration."""
    return {
        "cassette_library_dir": "gencove/tests/files/vcr",
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
            filter_file_types_request,
        ],
        "before_record_response": [
            filter_jwt,
        ],
    }


@pytest.mark.vcr
@assert_authorization
def test_list_empty(mocker, credentials):
    """Test empty file types list"""
    runner = CliRunner()
    mocked_get_file_types = mocker.patch.object(
        APIClient,
        "get_file_types",
        return_value=FileTypesModel(results=[], meta=dict(next=None)),
    )
    res = runner.invoke(list_file_types, credentials)
    assert res.exit_code == 0
    mocked_get_file_types.assert_called_once()
    assert "" in res.output


@pytest.mark.vcr
@assert_authorization
def test_list_file_types_bad_project_id(
    mocker, credentials
):  # pylint: disable=unused-argument
    """Test file types throw an error if project is not uuid."""
    runner = CliRunner()

    project_id = "test"
    res = runner.invoke(list_file_types, ["--project-id", project_id, *credentials])
    assert res.exit_code == 1
    assert "ERROR: Project ID is not valid. Exiting." in res.output


@pytest.mark.vcr
@assert_authorization
def test_list_file_types_project_doesnt_exist(mocker, credentials, recording, vcr):
    """Test file types throw an error if no project doesn't exist."""
    runner = CliRunner()
    if not recording:
        file_types_response = get_vcr_response(
            "/api/v2/file-types/",
            vcr,
            operator.contains,
            just_body=False,
        )
        mocked_get_file_types = mocker.patch.object(
            APIClient,
            "get_file_types",
            side_effect=APIClientError(
                message="API Client Error: Not Found: Not found.",
                status_code=file_types_response["status"]["code"],
            ),
            return_value=file_types_response["body"]["string"],
        )

    project_id = str(uuid4())

    res = runner.invoke(
        list_file_types,
        ["--project-id", project_id, *credentials],
    )
    assert res.exit_code == 1
    assert (
        "\n".join(
            [
                f"ERROR: Project {project_id} does not exist.",
                "ERROR: API Client Error: Not Found: Not found.",
                "Aborted!\n",
            ]
        )
        == res.output
    )
    if not recording:
        mocked_get_file_types.assert_called_once()


@pytest.mark.vcr
@assert_authorization
@pytest.mark.parametrize("object_param", [None, "sample"])
def test_list_file_types_no_project(mocker, credentials, recording, vcr, object_param):
    """Test file types returns all sample file types if no project is given."""
    runner = CliRunner()
    if not recording:
        # Mock list_file_types only if using cassettes since return value is mocked.
        file_types_response = get_vcr_response(
            "/api/v2/file-types/", vcr, operator.contains
        )
        mocked_get_file_types = mocker.patch.object(
            APIClient,
            "get_file_types",
            return_value=FileTypesModel(**file_types_response),
        )
    args = [*credentials]
    if object_param is not None:
        args.extend(["--object", object_param])
    res = runner.invoke(list_file_types, [*args])
    assert res.exit_code == 0
    if not recording:
        mocked_get_file_types.assert_called_once()
        file_types = file_types_response["results"]
        file_types = "\n".join(
            [
                "\t".join(
                    [
                        file_type["key"],
                        file_type["description"],
                    ]
                )
                for file_type in sorted(file_types, key=lambda ft: ft["key"])
            ]
        )
        assert f"{file_types}\n" == res.output


@pytest.mark.vcr
@assert_authorization
@pytest.mark.parametrize("object_param", [None, "sample"])
def test_list_file_types_by_project(
    mocker, credentials, project_id, recording, vcr, object_param
):
    """Test file types being outputted to the shell"""
    runner = CliRunner()

    if not recording:
        # Mock list_file_types only if using cassettes since return value is mocked.
        file_types_response = get_vcr_response(
            "/api/v2/file-types/", vcr, operator.contains
        )
        mocked_get_file_types = mocker.patch.object(
            APIClient,
            "get_file_types",
            return_value=FileTypesModel(**file_types_response),
        )
    args = ["--project-id", project_id, *credentials]
    if object_param is not None:
        args.extend(["--object", object_param])
    res = runner.invoke(list_file_types, [*args])

    assert res.exit_code == 0

    if not recording:
        mocked_get_file_types.assert_called_once()
        file_types = file_types_response["results"]
        file_types = "\n".join(
            [
                "\t".join(
                    [
                        file_type["key"],
                        file_type["description"],
                    ]
                )
                for file_type in sorted(file_types, key=lambda ft: ft["key"])
            ]
        )
        assert f"{file_types}\n" == res.output


@pytest.mark.vcr
@assert_authorization
def test_list_file_types_no_project_reference_genome(
    mocker, credentials, recording, vcr
):
    """Test file types returns all reference genome types if no project is given."""
    runner = CliRunner()
    if not recording:
        # Mock list_file_types only if using cassettes since return value is mocked.
        file_types_response = get_vcr_response(
            "/api/v2/file-types/", vcr, operator.contains
        )
        mocked_get_file_types = mocker.patch.object(
            APIClient,
            "get_file_types",
            return_value=FileTypesModel(**file_types_response),
        )
    res = runner.invoke(list_file_types, ["--object", "reference_genome", *credentials])
    assert res.exit_code == 0
    if not recording:
        mocked_get_file_types.assert_called_once_with(object_param="reference_genome")
        file_types = file_types_response["results"]
        file_types = "\n".join(
            [
                "\t".join(
                    [
                        file_type["key"],
                        file_type["description"],
                    ]
                )
                for file_type in sorted(file_types, key=lambda ft: ft["key"])
            ]
        )
        assert f"{file_types}\n" == res.output


@pytest.mark.vcr
@assert_authorization
def test_list_file_types_by_project_reference_genome(
    mocker, credentials, project_id, recording, vcr
):
    """Test that no ouput is given if Project doesn't have a Reference Genome."""
    runner = CliRunner()
    if not recording:
        # Mock list_file_types only if using cassettes since return value is mocked.
        file_types_response = get_vcr_response(
            "/api/v2/file-types/", vcr, operator.contains
        )
        mocked_get_file_types = mocker.patch.object(
            APIClient,
            "get_file_types",
            return_value=FileTypesModel(**file_types_response),
        )
    res = runner.invoke(
        list_file_types,
        ["--object", "reference_genome", "--project-id", project_id, *credentials],
    )

    assert res.exit_code == 0
    if not recording:
        mocked_get_file_types.assert_called_once_with(
            project_id=project_id, object_param="reference_genome"
        )
        file_types = file_types_response["results"]
        file_types = "\n".join(
            [
                "\t".join(
                    [
                        file_type["key"],
                        file_type["description"],
                    ]
                )
                for file_type in sorted(file_types, key=lambda ft: ft["key"])
            ]
        )
        assert f"{file_types}" == res.output
