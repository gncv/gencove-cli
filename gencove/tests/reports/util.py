"""Shared test code for reports"""

from requests import Response


def get_response_from_vcr_dict(vcr_dict: dict) -> Response:
    """Create Response object from get_vcr_response return value"""
    response = Response()
    response.status_code = vcr_dict["status"]["code"]
    response.headers = vcr_dict["headers"]
    content_disposition = response.headers.get("Content-Disposition")
    if content_disposition:
        response.headers["content-disposition"] = content_disposition[0]
    response._content = vcr_dict["body"]["string"]  # pylint: disable=protected-access
    return response
