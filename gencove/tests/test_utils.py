"""Tests for utils of Gencove CLI."""
# pylint: disable=wrong-import-order, import-error

import csv
import os
from enum import Enum

from click import Abort
from click.core import Argument, Option
from click.testing import CliRunner

from faker import Faker

from gencove.client import APIClient, APIClientError
from gencove.command.download.utils import (
    _get_prefix_parts,
    build_file_path,
    get_download_template_format_params,
)
from gencove.command.upload.utils import (
    _validate_header,
    parse_fastqs_map_file,
    upload_file,
)
from gencove.command.utils import is_valid_uuid, validate_uuid, validate_uuid_list
from gencove.constants import (
    ApiEndpoints,
    Credentials,
    DOWNLOAD_TEMPLATE,
    DownloadTemplateParts,
)
from gencove.exceptions import MaintenanceError, ValidationError
from gencove.utils import enum_as_dict, login

import pytest

fake = Faker()


def test_upload_file(mocker):
    """Sanity check upload function."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("foo.txt", "w", encoding="utf-8") as fastq_file:
            fastq_file.write("AAABBB")
        mocked_s3_client = mocker.Mock()
        assert upload_file(
            mocked_s3_client,
            "foo.txt",
            "foo-bucket",
            object_name="foo-object.txt",
        )
        mocked_s3_client.upload_file.assert_called_once()


def test_download_template_tokens():
    """Ensure download tokens are only the ones defined."""
    assert [
        "client_id",
        "gencove_id",
        "file_type",
        "file_extension",
        "default_filename",
    ] == list(enum_as_dict(DownloadTemplateParts).values())


# pylint: disable=too-many-locals
def test_build_file_path():
    """Test token combinations when building a file path."""
    client_id = "12345"
    gencove_id = "1"
    deliverable = {
        "download_url": "https://example.com/file.txt",
        "file_type": "txt",
    }
    download_template_format_params = get_download_template_format_params(
        client_id, gencove_id
    )
    # file with prefix will never have client_id and gencove_id. 0 is default
    file_with_prefix0 = (
        f"{download_template_format_params['client_id']}/"
        f"{download_template_format_params['gencove_id']}/"
        f"{download_template_format_params['default_filename']}"
    )
    file_with_prefix1 = download_template_format_params["client_id"]
    file_with_prefix2 = download_template_format_params["gencove_id"]
    file_with_prefix3 = "{file_type}"
    file_with_prefix4 = "{file_extension}"
    file_with_prefix5 = "{default_filename}"
    file_with_prefix6 = "{default_filename}.{file_extension}"
    file_with_prefix7 = (
        f"{download_template_format_params['default_filename']}."
        f"{download_template_format_params['client_id']}"
    )
    file_with_prefix8 = (
        f"{download_template_format_params['client_id']}."
        f"{download_template_format_params['default_filename']}"
    )
    file_with_prefix9 = (
        f"{download_template_format_params['file_extension']}_"
        f"{download_template_format_params['client_id']}"
    )
    download_to = "."
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = build_file_path(deliverable, file_with_prefix0, download_to)
        # default_filename is always a full filename with any extensions
        assert result == (
            f"./{download_template_format_params['client_id']}/"
            f"{download_template_format_params['gencove_id']}/file.txt"
        )
        result = build_file_path(deliverable, file_with_prefix1, download_to)
        assert result == f"./{download_template_format_params['client_id']}"
        result = build_file_path(deliverable, file_with_prefix2, download_to)
        assert result == f"./{download_template_format_params['gencove_id']}"
        result = build_file_path(deliverable, file_with_prefix3, download_to)
        assert result == "./txt"
        result = build_file_path(deliverable, file_with_prefix4, download_to)
        assert result == "./txt"
        result = build_file_path(deliverable, file_with_prefix5, download_to)
        assert result == "./file.txt"
        result = build_file_path(deliverable, file_with_prefix6, download_to)
        assert result == "./file.txt.txt"
        result = build_file_path(deliverable, file_with_prefix7, download_to)
        assert result == f"./file.txt.{download_template_format_params['client_id']}"
        result = build_file_path(deliverable, file_with_prefix8, download_to)
        assert result == f"./{download_template_format_params['client_id']}.file.txt"
        result = build_file_path(deliverable, file_with_prefix9, download_to)
        assert result == f"./txt_{download_template_format_params['client_id']}"


def test___get_filename_dirs_prefix():
    """Test proper processing of parts in download template."""
    client_id = "12345"
    gencove_id = "1"
    download_template_format_params = get_download_template_format_params(
        client_id, gencove_id
    )
    template = DOWNLOAD_TEMPLATE.format(**download_template_format_params)

    resp = _get_prefix_parts(template)

    assert resp.dirs == (
        f"{download_template_format_params['client_id']}/"
        f"{download_template_format_params['gencove_id']}"
    )
    assert resp.filename == f"{{{DownloadTemplateParts.DEFAULT_FILENAME.value}}}"
    assert resp.file_extension == ""

    template2 = (
        f"{download_template_format_params['client_id']}-"
        f"{download_template_format_params['gencove_id']}_"
        f"{download_template_format_params['file_type']}"
    )
    resp = _get_prefix_parts(template2)
    assert resp.dirs == ""
    assert resp.filename == (
        f"{download_template_format_params['client_id']}-"
        f"{download_template_format_params['gencove_id']}_"
        f"{{{DownloadTemplateParts.FILE_TYPE.value}}}"
    )
    assert resp.file_extension == ""

    template3 = (
        f"{download_template_format_params['client_id']}-"
        f"{download_template_format_params['gencove_id']}_"
        f"{download_template_format_params['file_type']}.vcf.gz"
    )
    resp = _get_prefix_parts(template3)
    assert resp.dirs == ""
    assert resp.filename == (
        f"{download_template_format_params['client_id']}-"
        f"{download_template_format_params['gencove_id']}_"
        f"{{{DownloadTemplateParts.FILE_TYPE.value}}}"
    )
    assert resp.file_extension == "vcf.gz"


def test_parse_fastqs_map_file():
    """Test parsing of map file into dict."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        os.mkdir("test_dir")
        with open("test_dir/test.fastq.gz", "w", encoding="utf-8") as fastq_file1:
            fastq_file1.write("AAABBB")

        with open("test_dir/test_2.fastq.gz", "w", encoding="utf-8") as fastq_file2:
            fastq_file2.write("AAABBB")

        with open("test_dir/test_3.fastq.gz", "w", encoding="utf-8") as fastq_file3:
            fastq_file3.write("AAABBB")

        with open("test_map.csv", "w", encoding="utf-8") as map_file:
            writer = csv.writer(map_file)
            writer.writerows(
                [
                    ["client_id", "r_notation", "path"],
                    ["barid", "r1", "test_dir/test.fastq.gz"],
                    ["barid", "r2", "test_dir/test_2.fastq.gz"],
                    ["barid", "r1", "test_dir/test_3.fastq.gz"],
                ]
            )

        fastqs = parse_fastqs_map_file("test_map.csv")
        assert len(fastqs) == 2
        assert ("barid", "R1") in fastqs
        assert ("barid", "R2") in fastqs
        assert len(fastqs[("barid", "R1")]) == 2
        assert fastqs[("barid", "R1")][0] == "test_dir/test.fastq.gz"
        assert fastqs[("barid", "R1")][1] == "test_dir/test_3.fastq.gz"


def test_invalid_fastqs_map_file():
    """Test that error is raised if file is invalid."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        os.mkdir("test_dir")
        with open("test_dir/test.fastq.gz", "w", encoding="utf-8") as fastq_file1:
            fastq_file1.write("AAABBB")

        with open("test_dir/test_2.fastq.gz", "w", encoding="utf-8") as fastq_file2:
            fastq_file2.write("AAABBB")

        with open("test_dir/test_3.fastq.gz", "w", encoding="utf-8") as fastq_file3:
            fastq_file3.write("AAABBB")

        with open("test_map.csv", "w", encoding="utf-8") as map_file:
            writer = csv.writer(map_file)
            writer.writerows(
                [
                    ["client_id", "r_notation", "path"],
                    ["barid", "r1", "test_dir/test.fastq.gz"],
                    ["barid", "r2", "test_dir/test_2.fastq.zip"],
                    ["barid", "r1", "test_dir/test_3.fastq.gz"],
                ]
            )
        try:
            parse_fastqs_map_file("test_map.csv")
        except ValidationError as err:
            assert "Bad file extension in path" in err.args[0]


def test_fastqs_map_file_path_does_not_exist():
    """Test that error is raised if file is invalid."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        os.mkdir("test_dir")
        with open("test_dir/test.fastq.gz", "w", encoding="utf-8") as fastq_file1:
            fastq_file1.write("AAABBB")

        with open("test_dir/test_2.fastq.gz", "w", encoding="utf-8") as fastq_file2:
            fastq_file2.write("AAABBB")

        with open("test_dir/test_3.fastq.gz", "w", encoding="utf-8") as fastq_file3:
            fastq_file3.write("AAABBB")

        with open("test_map.csv", "w", encoding="utf-8") as map_file:
            writer = csv.writer(map_file)
            writer.writerows(
                [
                    ["client_id", "r_notation", "path"],
                    ["barid", "r1", "test_dir/test.fastq.gz"],
                    ["barid", "r1", "test_dir/test_3.fastq.gz"],
                    ["barid", "r1", "test_dir/i_dont_exist.fastq.gz"],
                ]
            )
        try:
            parse_fastqs_map_file("test_map.csv")
        except ValidationError as err:
            assert "Could not find" in err.args[0]


def test_fastqs_map_file_has_wrong_header():
    """Test that header is validated properly."""
    runner = CliRunner()
    # This context manager is used to avoid unnecessarily creating a
    # test_map.csv file in the root of the project on every test run
    with runner.isolated_filesystem():
        with open("test_map.csv", "w", encoding="utf-8") as map_file:
            writer = csv.writer(map_file)
            writer.writerows(
                [
                    ["client_id", "r1_notation", "path"],
                    ["barid", "r1", "test_dir/test.fastq.gz"],
                    ["barid", "r1", "test_dir/test_3.fastq.gz"],
                    ["barid", "r1", "test_dir/i_dont_exist.fastq.gz"],
                ]
            )
        try:
            parse_fastqs_map_file("test_map.csv")
        except ValidationError as err:
            assert "Unexpected CSV header" in err.args[0]


def test__validate_header():
    """Test that header is validated properly."""
    header_row = dict(foo="foo", bar="bar")
    try:
        _validate_header(header_row)
    except ValidationError:
        pass

    # expected
    header_row = dict(client_id="client_id", r_notation="r_notation", path="path")
    assert _validate_header(header_row) is None

    # with spacing
    header_row = dict(client_id="client_id", r_notation=" r_notation", path="path  ")
    assert _validate_header(header_row) is None

    # with uppercase
    header_row = dict(client_id="client_id", r_notation="R_notation", path="path")
    assert _validate_header(header_row) is None


def test_is_valid_uuid__is_valid():
    """Test that a UUID is a valid UUID"""
    assert is_valid_uuid("11111111-1111-1111-1111-111111111111")


def test_is_valid_uuid__is_not_valid__too_long():
    """Test that UUID with extra chars is not a valid UUID"""
    assert is_valid_uuid("11111111-1111-1111-1111-11111111111122") is False


def test_is_valid_uuid__is_not_valid__too_short():
    """Test that UUID with missing chars is not a valid UUID"""
    assert is_valid_uuid("11111111-1111-1111-1111-1") is False


def test_is_valid_uuid__is_not_valid__text():
    """Test that random word is not a valid UUID"""
    assert is_valid_uuid("foo") is False


def test_enum_as_dict():
    """Test that the function enum_as_dict returns properly formatted dict."""

    class TestEnum(Enum):
        """Enum for testing"""

        KEY1 = "key1"
        KEY2 = "key2"
        KEY3 = "key3"

    assert enum_as_dict(TestEnum) == {
        "KEY1": "key1",
        "KEY2": "key2",
        "KEY3": "key3",
    }


def test_login_mfa(mocker):
    """Test that the the login function in APIClient asks for the one time
    password token.
    """
    api_client = APIClient()
    credentials = Credentials(email="foo@bar.com", password="123456", api_key="")

    def _request(
        endpoint,
        params,
        *args,  # pylint: disable=unused-argument
        **kwargs,  # pylint: disable=unused-argument
    ):
        if endpoint == ApiEndpoints.GET_JWT.value:
            if "otp_token" not in params:
                raise APIClientError(
                    {"otp_token": ["Please enter your OTP token."]}, 401
                )
            return {"access": "access", "refresh": "refresh"}
        return {}

    mocked_request = mocker.patch.object(APIClient, "_request", side_effect=_request)
    mocked_prompt = mocker.patch("gencove.utils.click.prompt", return_value="token")

    login(api_client, credentials)
    assert mocked_request.call_count == 2
    mocked_prompt.assert_called_once_with("One time password", type=str, err=True)


def test_login__returns_maintenance_error_message(mocker):
    """Test that the the login function in APIClient asks for the one time
    password token.
    """
    api_client = APIClient()
    credentials = Credentials(email="foo@bar.com", password="123456", api_key="")

    def _request(
        endpoint,
        params,
        *args,  # pylint: disable=unused-argument
        **kwargs,  # pylint: disable=unused-argument
    ):
        if endpoint == ApiEndpoints.GET_JWT.value:
            raise MaintenanceError(
                {
                    "maintenance": True,
                    "maintenance_eta": "",
                    "maintenance_message": (
                        "Gencove is currently undergoing maintenance and"
                        "will return at the given ETA."
                        "Thank you for your patience."
                    ),
                },
                503,
            )
        return {}

    mocked_request = mocker.patch.object(APIClient, "_request", side_effect=_request)

    with pytest.raises(MaintenanceError):
        login(api_client, credentials)
    mocked_request.assert_called_once()


def test_uuid_without_hyphens_is_converted_to_uuid_with_hyphens():
    """Test that when a uuid without hyphens is passed to the method, it
    will automatically add the hyphens
    """
    expected_uuid = str(fake.uuid4())
    input_uuid_without_hyphens = expected_uuid.replace("-", "")

    param = Argument(["-project_id"])
    actual_uuid = validate_uuid(None, param, input_uuid_without_hyphens)

    assert isinstance(actual_uuid, str)
    assert actual_uuid == expected_uuid


def test_uuid_with_hyphens_remains_as_is():
    """Test that when uuid with hyphens it will not do anything"""
    input_uuid = fake.uuid4()
    expected_uuid = str(input_uuid)

    param = Argument(["-project_id"])
    actual_uuid = validate_uuid(None, param, input_uuid)

    assert isinstance(actual_uuid, str)
    assert actual_uuid == expected_uuid


def test_uuid_with_hyphens_remains_as_is__not_v4_uuid():
    """Test that when uuid with hyphens it will not do anything even for values
    that are not technically a uuid v4.
    """
    input_uuid = "11111111-1111-1111-1111-111111111234"
    expected_uuid = str(input_uuid)

    param = Argument(["-project_id"])
    actual_uuid = validate_uuid(None, param, input_uuid)

    assert isinstance(actual_uuid, str)
    assert actual_uuid == expected_uuid


def test_validate_uuid__raises_if_uuid_invalid():
    """Test that an invalid uuid will raise a click.Abort"""
    input_uuid = "codef00d-1111-abcd-1111"

    param = Argument(["-project_id"])
    with pytest.raises(Abort):
        validate_uuid(None, param, input_uuid)


def test_validate_uuid_list__returns_list_of_valid_uuids():
    """Test string of valid uuids returns list of valid uuids"""
    param = Option(["-sample_ids"], nargs=1, multiple=False, default=None)
    valid_uuid_list = fake.pylist(nb_elements=3, value_types=("uuid4",))
    valid_uuids_string = ",".join(valid_uuid_list)
    validation_result = validate_uuid_list(None, param, valid_uuids_string)

    assert isinstance(validation_result, list)
    assert len(validation_result) == len(valid_uuid_list)


def test_validate_uuid_list__raises_if_not_all_ids_valid():
    """Test uuid list containing one invalid uuid will raise a click.Abort"""
    invalid_uuid = "codef00d-1111-abcd-1111"
    param = Option(["-sample_ids"], nargs=1, multiple=False, default=None)
    valid_uuid_list = fake.pylist(nb_elements=3, value_types=("uuid4",))
    valid_uuids_string = ",".join(valid_uuid_list)
    uuids_string = f"{valid_uuids_string},{invalid_uuid}"

    with pytest.raises(Abort):
        validate_uuid_list(None, param, uuids_string)
