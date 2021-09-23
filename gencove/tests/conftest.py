# This file needs to be called conftest.py. See:
# https://docs.pytest.org/en/6.2.x/fixture.html#conftest-py-sharing-fixtures-across-multiple-files
"""Common fixtures."""

# pylint: disable=import-error

import os

import pytest


@pytest.fixture(scope="session")
def using_api_key():
    """Returns True if API Key is being used."""
    api_key = os.getenv("GENCOVE_API_KEY_TEST")
    return api_key is not None


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
def credentials():
    """Fixture to have the appropriate credentials."""
    api_key = os.getenv("GENCOVE_API_KEY_TEST")
    email = os.getenv("GENCOVE_EMAIL_TEST")
    password = os.getenv("GENCOVE_PASSWORD_TEST")
    if api_key:
        return ["--api-key", api_key]
    return ["--email", email, "--password", password]
