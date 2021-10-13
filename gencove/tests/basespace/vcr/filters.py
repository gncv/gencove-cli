"""VCR filters for basespace tests."""

from gencove.tests.decorators import parse_response_to_json
from gencove.tests.utils import MOCK_UUID


@parse_response_to_json
def filter_volatile_dates(response, json_response):
    """Patches volatile dates, and push them into the future, otherwise
    the app will think the token/whatever is expired.
    """
    if "expiry_time" in json_response:
        json_response["expiry_time"] = "2050-09-03T00:00:00+00:00"
    return response, json_response


def _filter_basespace_autoimport_list(result):
    """Common function that filters basespace autoimport job sensitive data."""
    if "project_id" in result:
        result["project_id"] = MOCK_UUID
    if "id" in result:
        result["id"] = MOCK_UUID
    if "identifier" in result:
        result["identifier"] = "mock_identifier"
    if "metadata" in result:
        result["identifier"] = {}


@parse_response_to_json
def filter_basespace_autoimport_list_response(response, json_response):
    """Filter BaseSpace autoimport sensitive data from response."""
    if "results" in json_response:
        for result in json_response["results"]:
            _filter_basespace_autoimport_list(result)
    return response, json_response
