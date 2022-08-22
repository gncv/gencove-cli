"""Test basespace projects list command."""
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
from gencove.command.basespace.projects.cli import basespace_list
from gencove.models import (
    BaseSpaceProject,
    BaseSpaceProjectDetail,
)


def test_basespace_list__empty(mocker):
    """Test user has no BaseSpace projects."""
    runner = CliRunner()
    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_list_basespace_projects = mocker.patch.object(
        APIClient,
        "list_basespace_projects",
        return_value=BaseSpaceProject(results=[], meta=dict(next=None)),
    )
    res = runner.invoke(basespace_list, ["--email", "foo@bar.com", "--password", "123"])
    assert res.exit_code == 0
    mocked_login.assert_called_once()
    mocked_list_basespace_projects.assert_called_once()
    assert "" in res.output


MOCKED_BASESPACE_PROJECTS = dict(
    meta=dict(next=None),
    results=[
        {
            "basespace_id": "1234",
            "basespace_name": "test\tproject",
            "basespace_date_created": (
                datetime.utcnow() - timedelta(days=7)
            ).isoformat(),
        }
    ],
)

# API responses may return new keys and values eventually
MOCKED_BASESPACE_PROJECTS_WITH_UNEXPECTED_KEYS = dict(
    meta=dict(next=None),
    results=[
        {
            "basespace_id": "1234",
            "basespace_name": "test\tproject",
            "basespace_description": "",
            "basespace_date_created": (
                datetime.utcnow() - timedelta(days=7)
            ).isoformat(),
        }
    ],
)


def test_basespace_list__no_permission(mocker):
    """Test BaseSpace projects no permission available to show them."""
    runner = CliRunner()
    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_list_basespace_projects = mocker.patch.object(
        APIClient,
        "list_basespace_projects",
        side_effect=APIClientError(
            message="API Client Error: Not Found: Not found.", status_code=403
        ),
        return_value={"detail": "Not found"},
    )
    res = runner.invoke(basespace_list, ["--email", "foo@bar.com", "--password", "123"])
    assert res.exit_code == 1
    mocked_login.assert_called_once()
    mocked_list_basespace_projects.assert_called_once()

    output_line = io.BytesIO()
    sys.stdout = output_line
    echo(
        "\n".join(
            [
                "ERROR: There was an error listing BaseSpace projects.",
                "ERROR: You do not have the sufficient permission "
                "level required to perform this operation.",
                "ERROR: API Client Error: Not Found: Not found.",
                "Aborted!",
            ]
        )
    )
    assert output_line.getvalue() == res.output.encode()


def test_basespace_list__slow_response_retry_list(mocker):
    """Test BaseSpace projects slow response retry on the list."""
    runner = CliRunner()
    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_list_basespace_projects = mocker.patch.object(
        APIClient,
        "list_basespace_projects",
        side_effect=APIClientTimeout("Could not connect to the api server"),
    )
    res = runner.invoke(basespace_list, ["--email", "foo@bar.com", "--password", "123"])
    assert res.exit_code == 1
    mocked_login.assert_called_once()
    assert mocked_list_basespace_projects.call_count == 2


def test_basespace_list(mocker):
    """Test BaseSpace projects being outputed to the shell."""
    runner = CliRunner()
    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_list_basespace_projects = mocker.patch.object(
        APIClient,
        "list_basespace_projects",
        return_value=BaseSpaceProject(**MOCKED_BASESPACE_PROJECTS),
    )
    res = runner.invoke(basespace_list, ["--email", "foo@bar.com", "--password", "123"])
    assert res.exit_code == 0
    mocked_login.assert_called_once()
    mocked_list_basespace_projects.assert_called_once()

    basespace_project = BaseSpaceProjectDetail(
        **MOCKED_BASESPACE_PROJECTS["results"][0]
    )

    output_line = io.BytesIO()
    sys.stdout = output_line
    echo(
        "\t".join(
            [
                str(basespace_project.basespace_date_created),
                str(basespace_project.basespace_id),
                basespace_project.basespace_name.replace("\t", " "),
            ]
        )
    )
    assert output_line.getvalue() == res.output.encode()


def test_basespace_list__with_unexpected_keys(mocker):
    """Test BaseSpace projects being outputed to the shell with
    an unexpected key as a part of the response.
    """

    runner = CliRunner()
    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    mocked_list_basespace_projects = mocker.patch.object(
        APIClient,
        "list_basespace_projects",
        return_value=BaseSpaceProject(**MOCKED_BASESPACE_PROJECTS_WITH_UNEXPECTED_KEYS),
    )
    res = runner.invoke(basespace_list, ["--email", "foo@bar.com", "--password", "123"])
    assert res.exit_code == 0
    mocked_login.assert_called_once()
    mocked_list_basespace_projects.assert_called_once()

    basespace_project = BaseSpaceProjectDetail(
        **MOCKED_BASESPACE_PROJECTS_WITH_UNEXPECTED_KEYS["results"][0]
    )

    output_line = io.BytesIO()
    sys.stdout = output_line
    echo(
        "\t".join(
            [
                str(basespace_project.basespace_date_created),
                str(basespace_project.basespace_id),
                basespace_project.basespace_name.replace("\t", " "),
            ]
        )
    )
    assert output_line.getvalue() == res.output.encode()
