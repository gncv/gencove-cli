"""Test basespace biosamples list command."""
# pylint: disable=wrong-import-order
import io
import sys
from datetime import datetime, timedelta

from click import echo
from click.testing import CliRunner

from gencove.client import (
    APIClient,
    APIClientError,
    APIClientTimeout,
)  # noqa: I100
from gencove.command.basespace.biosamples.cli import biosamples_list
from gencove.models import (
    BaseSpaceBiosample,
    BaseSpaceBiosampleDetail,
)


def test_biosamples_list__empty(mocker):
    """Test user has no BaseSpace Biosamples."""
    runner = CliRunner()
    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_list_biosamples = mocker.patch.object(
        APIClient,
        "list_biosamples",
        return_value=BaseSpaceBiosample(results=[], meta=dict(next=None)),
    )
    res = runner.invoke(
        biosamples_list,
        ["1234", "--email", "foo@bar.com", "--password", "123"],
    )
    assert res.exit_code == 0
    mocked_login.assert_called_once()
    mocked_list_biosamples.assert_called_once()
    assert "" in res.output


MOCKED_BASESPACE_BIOSAMPLES = dict(
    meta=dict(next=None),
    results=[
        {
            "basespace_id": "1234",
            "basespace_bio_sample_name": "test\tproject",
            "basespace_date_created": (
                datetime.utcnow() - timedelta(days=7)
            ).isoformat(),
        }
    ],
)

# API responses may return new keys and values eventually
MOCKED_BASESPACE_BIOSAMPLES_WITH_UNEXPECTED_KEYS = dict(
    meta=dict(next=None),
    results=[
        {
            "basespace_id": "1234",
            "basespace_bio_sample_name": "test\tproject",
            "basespace_description": "",
            "basespace_date_created": (
                datetime.utcnow() - timedelta(days=7)
            ).isoformat(),
        }
    ],
)


def test_biosamples_list__no_permission(mocker):
    """Test BaseSpace Biosamples no permission available to show them."""
    runner = CliRunner()
    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_list_biosamples = mocker.patch.object(
        APIClient,
        "list_biosamples",
        side_effect=APIClientError(
            message="API Client Error: Not Found: Not found.", status_code=403
        ),
        return_value={"detail": "Not found"},
    )
    res = runner.invoke(
        biosamples_list,
        ["1234", "--email", "foo@bar.com", "--password", "123"],
    )
    assert res.exit_code == 1
    mocked_login.assert_called_once()
    mocked_list_biosamples.assert_called_once()

    output_line = io.BytesIO()
    sys.stdout = output_line
    echo(
        "\n".join(
            [
                "ERROR: There was an error listing Biosamples.",
                "ERROR: You do not have the sufficient permission "
                "level required to perform this operation.",
                "ERROR: API Client Error: Not Found: Not found.",
                "Aborted!",
            ]
        )
    )
    assert output_line.getvalue() == res.output.encode()


def test_biosamples_list__slow_response_retry_list(mocker):
    """Test BaseSpace Biosamples slow response retry on the list."""
    runner = CliRunner()
    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_list_biosamples = mocker.patch.object(
        APIClient,
        "list_biosamples",
        side_effect=APIClientTimeout("Could not connect to the api server"),
    )
    res = runner.invoke(
        biosamples_list,
        ["1234", "--email", "foo@bar.com", "--password", "123"],
    )
    assert res.exit_code == 1
    mocked_login.assert_called_once()
    assert mocked_list_biosamples.call_count == 2


def test_biosamples_list__multiple(mocker):
    """Test BaseSpace Biosamples from multiple projects
    being outputed to the shell.
    """
    runner = CliRunner()
    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_list_biosamples = mocker.patch.object(
        APIClient,
        "list_biosamples",
        return_value=BaseSpaceBiosample(**MOCKED_BASESPACE_BIOSAMPLES),
    )
    res = runner.invoke(
        biosamples_list,
        ["1234,4321", "--email", "foo@bar.com", "--password", "123"],
    )
    assert res.exit_code == 0
    mocked_login.assert_called_once()
    mocked_list_biosamples.assert_called_once()

    basespace_project = BaseSpaceBiosampleDetail(
        **MOCKED_BASESPACE_BIOSAMPLES["results"][0]
    )

    output_line = io.BytesIO()
    sys.stdout = output_line
    echo(
        "\t".join(
            [
                str(basespace_project.basespace_date_created),
                str(basespace_project.basespace_id),
                basespace_project.basespace_bio_sample_name.replace("\t", " "),
            ]
        )
    )
    assert output_line.getvalue() == res.output.encode()


def test_biosamples_list(mocker):
    """Test BaseSpace Biosamples being outputed to the shell."""
    runner = CliRunner()
    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_list_biosamples = mocker.patch.object(
        APIClient,
        "list_biosamples",
        return_value=BaseSpaceBiosample(**MOCKED_BASESPACE_BIOSAMPLES),
    )
    res = runner.invoke(
        biosamples_list,
        ["1234", "--email", "foo@bar.com", "--password", "123"],
    )
    assert res.exit_code == 0
    mocked_login.assert_called_once()
    mocked_list_biosamples.assert_called_once()

    basespace_project = BaseSpaceBiosampleDetail(
        **MOCKED_BASESPACE_BIOSAMPLES["results"][0]
    )

    output_line = io.BytesIO()
    sys.stdout = output_line
    echo(
        "\t".join(
            [
                str(basespace_project.basespace_date_created),
                str(basespace_project.basespace_id),
                basespace_project.basespace_bio_sample_name.replace("\t", " "),
            ]
        )
    )
    assert output_line.getvalue() == res.output.encode()


def test_biosamples_list__with_unexpected_keys(mocker):
    """Test BaseSpace Biosamples being outputed to the shell with
    an unexpected key as a part of the response.
    """

    runner = CliRunner()
    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_list_biosamples = mocker.patch.object(
        APIClient,
        "list_biosamples",
        return_value=BaseSpaceBiosample(
            **MOCKED_BASESPACE_BIOSAMPLES_WITH_UNEXPECTED_KEYS
        ),
    )
    res = runner.invoke(
        biosamples_list,
        ["1234", "--email", "foo@bar.com", "--password", "123"],
    )
    assert res.exit_code == 0
    mocked_login.assert_called_once()
    mocked_list_biosamples.assert_called_once()

    basespace_project = BaseSpaceBiosampleDetail(
        **MOCKED_BASESPACE_BIOSAMPLES_WITH_UNEXPECTED_KEYS["results"][0]
    )

    output_line = io.BytesIO()
    sys.stdout = output_line
    echo(
        "\t".join(
            [
                str(basespace_project.basespace_date_created),
                str(basespace_project.basespace_id),
                basespace_project.basespace_bio_sample_name.replace("\t", " "),
            ]
        )
    )
    assert output_line.getvalue() == res.output.encode()
