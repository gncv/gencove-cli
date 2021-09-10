# This file needs to be called conftest.py.
# see: https://docs.pytest.org/en/6.2.x/fixture.html#conftest-py-sharing-fixtures-across-multiple-files

import os

import pytest


@pytest.fixture(scope="session")
def using_api_key():
    api_key = os.getenv("GENCOVE_API_KEY")
    return api_key is not None


@pytest.fixture(scope="session")
def recording(record_mode):
    """Returns True if VCR cassettes are being recorded.
    False if being played.
    """
    return record_mode != "none"


@pytest.fixture(scope="session")
def project_id(record_mode):
    return os.getenv("GENCOVE_PROJECT_ID")
