"""Tests for utils of Gencove CLI."""
from gencove.utils import upload_file


def test_upload_file(mocker):
    """Sanity check upload function."""
    mocked_s3_client = mocker.Mock()
    assert upload_file(
        mocked_s3_client,
        "foo.txt",
        "foo-bucket",
        object_name="foo-object.txt",
    )
    mocked_s3_client.upload_file.assert_called_once()
