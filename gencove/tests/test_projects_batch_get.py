"""Test project's batches list command."""

from uuid import uuid4

from click.testing import CliRunner

from gencove.client import APIClient  # noqa: I100
from gencove.command.projects.cli import get_batch


def test_get_batch__empty(mocker):
    """Test project has not batches."""
    runner = CliRunner()
    mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
    batch_id = str(uuid4())
    mocked_get_project_batches = mocker.patch.object(
        APIClient,
        "get_batch",
        return_value=dict(
            id=batch_id,
            name="cli-test-1",
            batch_type="batch-type-1",
            sample_ids=["sample-id-1", "sample-id-2"],
            last_status=dict(
                id="last-status-id-1",
                status="running",
                created="2020-08-02T22:13:54.547167Z",
            ),
            files=[],
        ),
    )

    res = runner.invoke(
        get_batch, [batch_id, "--email", "foo@bar.com", "--password", "123"]
    )
    assert res.exit_code == 1
    mocked_login.assert_called_once()
    mocked_get_project_batches.assert_called_once()
    assert (
        res.output
        == "There are no deliverables available for batch {}.\n".format(
            batch_id
        )
    )


# MOCKED_BATCHES = dict(
#     meta=dict(count=2, next=None),
#     results=[
#         {
#             "id": str(uuid4()),
#             "name": "foo",
#             "batch_type": "hd777k",
#             "files": [
#                 {
#                     "id": str(uuid4()),
#                     "file_type": "report-zip",
#                     "download_url": "https://foo.com/bar.zip",
#                 }
#             ],
#         },
#         {
#             "id": str(uuid4()),
#             "name": "bar",
#             "batch_type": "hd777k",
#             "files": [
#                 {
#                     "id": str(uuid4()),
#                     "file_type": "report-zip",
#                     "download_url": "https://baz.com/bar.zip",
#                 }
#             ],
#         },
#     ],
# )


# def test_get_batch__not_empty(mocker):
#     """Test project batches being outputed to the shell."""
#     runner = CliRunner()
#     mocked_login = mocker.patch.object(APIClient, "login", return_value=None)
#     mocked_get_project_batches = mocker.patch.object(
#         APIClient, "get_project_batches", return_value=MOCKED_BATCHES
#     )

#     res = runner.invoke(
#         get_batch,
#         [str(uuid4()), "--email", "foo@bar.com", "--password", "123"],
#     )
#     assert res.exit_code == 0
#     mocked_login.assert_called_once()
#     mocked_get_project_batches.assert_called_once()

#     output_line = io.BytesIO()
#     sys.stdout = output_line
#     line_one = "\t".join(
#         [
#             MOCKED_BATCHES["results"][0]["id"],
#             MOCKED_BATCHES["results"][0]["batch_type"],
#             MOCKED_BATCHES["results"][0]["name"],
#         ]
#     )
#     line_two = "\t".join(
#         [
#             MOCKED_BATCHES["results"][1]["id"],
#             MOCKED_BATCHES["results"][1]["batch_type"],
#             MOCKED_BATCHES["results"][1]["name"],
#         ]
#     )
#     echo("\n".join([line_one, line_two]))
#     assert output_line.getvalue() == res.output.encode()
