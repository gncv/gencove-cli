import re

from gencove.tests.filters import _replace_uuid_from_url
from gencove.tests.utils import MOCK_UUID


def filter_project_qc_report_request(request):
    """Filter project UUID data from request."""
    return _replace_uuid_from_url(request, "project-qc-report")


def filter_monthly_usage_report_request(request):
    """Filter project UUID data from request."""
    return _replace_uuid_from_url(request, "monthly-usage")


def filter_report_response_body(response):
    """Filter out all UUIDs in the response body"""
    body = response["body"]["string"].decode()
    uuid_pattern = (
        r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
    )
    censored_body = re.sub(uuid_pattern, MOCK_UUID, body)
    response["body"]["string"] = censored_body.encode()
    return response


def filter_report_response_filename(response):
    if "Content-Disposition" in response["headers"]:
        response["headers"]["Content-Disposition"] = [
            'attachment; filename="report.csv"'
        ]
    return response
