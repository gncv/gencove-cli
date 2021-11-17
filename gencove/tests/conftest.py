# This file needs to be called conftest.py. See:
# https://docs.pytest.org/en/6.2.x/fixture.html#conftest-py-sharing-fixtures-across-multiple-files
"""Common fixtures."""

# pylint: disable=import-error

import os

import pytest


@pytest.fixture(scope="session")
def using_api_key():
    """Returns True if API Key is being used."""
    use_api_key = os.getenv("USING_API_KEY")
    return use_api_key is not None


@pytest.fixture(scope="session")
def recording(record_mode):
    """Returns True if VCR cassettes are being recorded.
    False if being played.
    """
    return record_mode != "none"


@pytest.fixture(scope="session")
def project_id():
    """Returns the project id."""
    return os.getenv("GENCOVE_PROJECT_ID")


@pytest.fixture(scope="session")
def project_id_batches():
    """Returns the project id that contains batches."""
    return os.getenv("GENCOVE_PROJECT_ID_BATCHES_TEST")


@pytest.fixture(scope="session")
def project_id_download():
    """Returns the project id that contains batches."""
    return os.getenv("GENCOVE_PROJECT_ID_DOWNLOAD_TEST")


@pytest.fixture(scope="session")
def credentials(using_api_key):  # pylint: disable=redefined-outer-name
    """Fixture to have the appropriate credentials."""
    api_key = os.getenv("GENCOVE_API_KEY_TEST")
    email = os.getenv("GENCOVE_EMAIL_TEST")
    password = os.getenv("GENCOVE_PASSWORD_TEST")
    if using_api_key:
        return ["--api-key", api_key]
    return ["--email", email, "--password", password]


@pytest.fixture(scope="session")
def archived_sample():
    """Returns the archived sample id.."""
    return os.getenv("GENCOVE_ARCHIVED_SAMPLE_TEST")


@pytest.fixture(scope="session")
def sample_id_batches():
    """Returns the sample id to create batches."""
    return os.getenv("GENCOVE_SAMPLE_ID_BATCHES_TEST")


@pytest.fixture(scope="session")
def sample_id_download():
    """Returns the sample id to download."""
    return os.getenv("GENCOVE_SAMPLE_ID_DOWNLOAD_TEST")


@pytest.fixture(scope="session")
def batch_type():
    """Returns the batch type to create batches."""
    return os.getenv("GENCOVE_BATCH_TYPE_TEST")


@pytest.fixture(scope="session")
def batch_name():
    """Returns the batch name to create batches."""
    return os.getenv("GENCOVE_BATCH_NAME_TEST")


@pytest.fixture(scope="session")
def batch_id():
    """Returns a batch id."""
    return os.getenv("GENCOVE_BATCH_ID_TEST")
