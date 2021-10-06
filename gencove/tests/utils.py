"""Util functions."""
import json
import operator

MOCK_UUID = "11111111-1111-1111-1111-111111111111"


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
    request = next(
        request for request in vcr.requests if matches(request.path, url)
    )
    response = vcr.responses_of(request)[0]
    if just_body:
        try:
            response = json.loads(response["body"]["string"])
        except json.decoder.JSONDecodeError:
            pass
    return response
