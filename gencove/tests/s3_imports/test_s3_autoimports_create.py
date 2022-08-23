"""Tests upload command of Gencove CLI."""
# pylint: disable=wrong-import-order, import-error

from uuid import uuid4

import pytest
from click.testing import CliRunner  # noqa: I100,I201
from gencove.client import APIClient, APIClientError  # noqa: I201
from gencove.command.s3_imports.autoimports.create.cli import create
from gencove.models import S3AutoimportTopic
from gencove.tests.decorators import assert_authorization
from gencove.tests.filters import filter_jwt, replace_gencove_url_vcr

from vcr import VCR


@pytest.fixture(scope="module")
def vcr_config():
    """VCR configuration."""
    return {
        "cassette_library_dir": "gencove/tests/s3_imports/vcr",
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
        ],
    }


@pytest.mark.default_cassette("jwt-create.yaml")
@pytest.mark.vcr
@assert_authorization
def test_s3_autoimport_create_project_id_not_uuid(
    credentials,
    mocker,
):
    """Test that project id is valid UUID when creating an automated import."""
    runner = CliRunner()

    mocked_autoimport_from_s3 = mocker.patch.object(
        APIClient,
        "autoimport_from_s3",
    )
    res = runner.invoke(
        create,
        [
            "1234",
            "identifier",
            *credentials,
        ],
    )

    assert res.exit_code == 1
    mocked_autoimport_from_s3.assert_not_called()
    assert "ERROR: Project ID is not valid. Exiting." in res.output


@pytest.mark.default_cassette("jwt-create.yaml")
@pytest.mark.vcr
@assert_authorization
def test_s3_autoimport_create_invalid_metadata(credentials, mocker, project_id):
    """Test that passed optional metadata is valid when creating an
    automated import.
    """
    runner = CliRunner()

    mocked_autoimport_from_s3 = mocker.patch.object(
        APIClient,
        "autoimport_from_s3",
    )
    res = runner.invoke(
        create,
        [
            project_id,
            "identifier",
            "--metadata-json",
            "[1,2,3",
            *credentials,
        ],
    )

    assert res.exit_code == 1
    mocked_autoimport_from_s3.assert_not_called()
    assert "ERROR: Metadata JSON is not valid. Exiting." in res.output


@pytest.mark.default_cassette("jwt-create.yaml")
@pytest.mark.vcr
@assert_authorization
def test_s3_autoimport_create_no_permission(credentials, mocker, project_id):
    """Test that user cannot create an automated import if no permissions."""
    runner = CliRunner()

    mocked_autoimport_from_s3 = mocker.patch.object(
        APIClient,
        "autoimport_from_s3",
        side_effect=APIClientError(message="", status_code=403),
    )
    res = runner.invoke(
        create,
        [
            project_id,
            "identifier",
            *credentials,
        ],
    )

    assert res.exit_code == 1
    mocked_autoimport_from_s3.assert_called_once()
    assert "There was an error creating an import job" in res.output


@pytest.mark.default_cassette("jwt-create.yaml")
@pytest.mark.vcr
@assert_authorization
def test_s3_autoimport_create_with_empty_metadata(credentials, mocker, project_id):
    """Test that user can pass empty metadata when creating an
    automated import.
    """
    runner = CliRunner()

    autoimport_from_s3 = S3AutoimportTopic(
        id=uuid4(), topic_arn="arn:aws:sns:us-east-1:123456789012:MyTopic"
    )

    mocked_autoimport_from_s3 = mocker.patch.object(
        APIClient,
        "autoimport_from_s3",
        return_value=autoimport_from_s3,
    )
    res = runner.invoke(
        create,
        [
            project_id,
            "s3://bucket/path/to/project/",
            "--metadata-json",
            None,
            *credentials,
        ],
    )

    assert res.exit_code == 0
    assert (
        "\t".join(
            [
                str(autoimport_from_s3.id),
                autoimport_from_s3.topic_arn,
            ]
        )
        in res.output
    )
    mocked_autoimport_from_s3.assert_called_once()


@pytest.mark.default_cassette("jwt-create.yaml")
@pytest.mark.vcr
@assert_authorization
def test_s3_autoimport_create_with_metadata(credentials, mocker, project_id):
    """Test that user can pass optional metadata when creating an
    automated import.
    """
    runner = CliRunner()

    autoimport_from_s3 = S3AutoimportTopic(
        id=uuid4(), topic_arn="arn:aws:sns:us-east-1:123456789012:MyTopic"
    )

    mocked_autoimport_from_s3 = mocker.patch.object(
        APIClient,
        "autoimport_from_s3",
        return_value=autoimport_from_s3,
    )
    res = runner.invoke(
        create,
        [
            project_id,
            "s3://bucket/path/to/project/",
            "--metadata-json",
            "[1,2,3]",
            *credentials,
        ],
    )

    assert res.exit_code == 0
    assert (
        "\t".join(
            [
                str(autoimport_from_s3.id),
                autoimport_from_s3.topic_arn,
            ]
        )
        in res.output
    )
    mocked_autoimport_from_s3.assert_called_once()


@pytest.mark.default_cassette("jwt-create.yaml")
@pytest.mark.vcr
@assert_authorization
def test_s3_autoimport_create_without_metadata(credentials, mocker, project_id):
    """Test that user can create an import job without passing metadata."""
    runner = CliRunner()

    autoimport_from_s3 = S3AutoimportTopic(
        id=uuid4(), topic_arn="arn:aws:sns:us-east-1:123456789012:MyTopic"
    )

    mocked_autoimport_from_s3 = mocker.patch.object(
        APIClient,
        "autoimport_from_s3",
        return_value=autoimport_from_s3,
    )
    res = runner.invoke(
        create,
        [
            project_id,
            "s3://bucket/path/to/project/",
            *credentials,
        ],
    )

    assert res.exit_code == 0
    assert (
        "\t".join(
            [
                str(autoimport_from_s3.id),
                autoimport_from_s3.topic_arn,
            ]
        )
        in res.output
    )
    mocked_autoimport_from_s3.assert_called_once()
