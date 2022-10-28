# This file needs to be called conftest.py. See:
# https://docs.pytest.org/en/6.2.x/fixture.html#conftest-py-sharing-fixtures-across-multiple-files
"""Common fixtures."""

# pylint: disable=import-error

import os
import uuid
from datetime import datetime

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
def pipeline_capability_id():
    """Returns the pipeline capability id."""
    return os.getenv("GENCOVE_PIPELINE_CAPABILITY_ID")


@pytest.fixture(scope="session")
def pipeline_id():
    """Returns the pipeline id."""
    return os.getenv("GENCOVE_PIPELINE_ID")


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
def deleted_sample():
    """Returns deleted sample id"""
    return os.getenv("GENCOVE_DELETED_SAMPLE_TEST")


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


@pytest.fixture(scope="session")
def sample_id_import_existing():
    """Returns a successful sample id."""
    return os.getenv("GENCOVE_SAMPLE_ID_IMPORT_EXISTING_TEST")


@pytest.fixture(scope="function", autouse=True)
def dont_save_dump_log():
    """Sets the environment variable to disable dumping the log file."""
    os.environ["GENCOVE_SAVE_DUMP_LOG"] = "FALSE"


@pytest.fixture(scope="function")
def dump_filename(mocker):
    """Fixtures that returns the log filename and creates the folder."""
    random_id = str(uuid.uuid4())
    now = datetime.utcnow()
    folder = f".logs/{now:%Y_%m}"
    filename = f"{folder}/{now:%Y_%m_%d_%H_%M_%S}_{random_id[:8]}.log"

    def get_debug_file_name_patch():
        os.makedirs(folder)
        return filename

    mocker.patch(
        "gencove.logger.get_debug_file_name",
        side_effect=get_debug_file_name_patch,
    )
    return filename


@pytest.fixture(scope="function")
def sample_archive_status_null():
    """A sample containing a NULL (eg. deleted) archive status"""
    return {
        "meta": {"count": 1, "next": None, "previous": None},
        "results": [
            {
                "id": "11111111-1111-1111-1111-111111111111",
                "created": "2021-09-21T18:30:44.799519Z",
                "modified": "2021-09-21T18:38:57.735776Z",
                "client_id": "mock client_id",
                "physical_id": "",
                "legacy_id": "",
                "last_status": {
                    "id": "11111111-1111-1111-1111-111111111111",
                    "status": "mock status",
                    "note": "",
                    "created": "2021-09-21T18:38:57.735776Z",
                },
                "archive_last_status": None,
            }
        ],
    }
