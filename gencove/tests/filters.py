from gencove.tests.decorators import parse_response_to_json


@parse_response_to_json
def filter_jwt(respose, response_json):
    if "refresh" in response_json and "access" in response_json:
        response_json["refresh"] = "mock_refresh"
        response_json["access"] = "mock_access"
    return respose, response_json
