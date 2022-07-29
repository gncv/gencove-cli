"""Test samples set metadata command."""

from uuid import uuid4

from click.testing import CliRunner

from gencove.client import APIClient
from gencove.command.projects.cli import import_existing_project_samples


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
    """Test import existing project samples failure when samples is a bad JSON."""
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
    """Test import existing project samples failure when samples JSON is not a list."""
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
    """Test import existing project samples failure when samples JSON is not a list of dicts."""
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


def test_import_existing_project_samples__bad_samples_content_no_key_in_dict_item(
    mocker,
):
    """Test import existing project samples failure when samples JSON dict item in a list doesn't
    have the sample_id key.
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


def test_import_existing_project_samples__bad_samples_bad_key_value_in_dict_item(
    mocker,
):
    """Test import existing project samples failure when samples JSON dict item in a list has
    the sample_id key with a bad value.
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


def test_import_existing_project_samples__bad_samples_bad_optional_key_value_in_dict_item(
    mocker,
):
    """Test import existing project samples failure when samples JSON dict item in a list has
    the optional client_id key with a bad value.
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
        "Client ID: {} for the sample {} is not valid. It cannot contain an underscore. Exiting.".format(
            bad_client_id, bad_sample_id
        )
        in res.output
    )


def test_import_existing_project_samples__bad_metadata(mocker):
    """Test import existing project samples failure when optional metadata-json is passed, but it
    has a bad value.
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
