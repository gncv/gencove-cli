import re

from gencove.tests.filters import _replace_uuid_from_url


def filter_project_qc_report_request(request):
    """Filter project UUID data from request."""
    return _replace_uuid_from_url(request, "project-qc-report")


def filter_project_qc_report_response_body(response):
    """Filter out all UUIDs in the response body"""
    body = response["body"]["string"].decode()
    uuid_pattern = (
        r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
    )
    censored_uuid = "11111111-1111-1111-1111-111111111111"
    censored_body = re.sub(uuid_pattern, censored_uuid, body)
    response["body"]["string"] = censored_body.encode()
    return response


def filter_project_qc_report_response_filename(response):
    if "Content-Disposition" in response["headers"]:
        response["headers"]["Content-Disposition"] = [
            'attachment; filename="project-qc-report.csv"'
        ]
    return response
