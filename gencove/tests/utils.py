"""Util functions."""
import json
import operator

from requests import Response
from requests.structures import CaseInsensitiveDict

MOCK_UUID = "11111111-1111-1111-1111-111111111111"
MOCK_CHECKSUM = "111111111111111111111111111111111111111111111111111111111111111a"


def get_vcr_response(url, vcr, matches=operator.eq, just_body=True):
    """Returns the VCR response of the first request that matches the url.

    Args:
        url (str): The request URL you want to match
        vcr (Cassette): VCR object, use the fixture
        matches (callable): Evaluator function
        just_body (bool): Set to False to retrieve the entire response object.

    Returns:
        response (dict): The VCR response.
    """
    request = next(request for request in vcr.requests if matches(request.path, url))
    response = vcr.responses_of(request)[0]
    if just_body:
        response = response["body"]["string"]
        try:
            response = json.loads(response)
        except json.decoder.JSONDecodeError:
            pass
    return response


def get_response_from_vcr_dict(vcr_dict: dict) -> Response:
    """Create Response object from get_vcr_response return value"""
    response = Response()
    response.status_code = vcr_dict["status"]["code"]
    response.headers = CaseInsensitiveDict(vcr_dict["headers"])
    response._content = vcr_dict["body"]["string"]  # pylint: disable=protected-access
    return response
