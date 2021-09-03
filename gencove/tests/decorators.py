import json
from functools import wraps


def parse_response_to_json(func):
    """Decorator that parses the response body into JSON and passes it to the
    function, then it saves the changes into the response body again.
    """

    @wraps(func)
    def wrapper(response):
        try:
            json_response = json.loads(response["body"]["string"])
        except json.decoder.JSONDecodeError:
            json_response = {}
        response, json_response = func(response, json_response)
        if response is not None and json_response:
            response["body"]["string"] = json.dumps(json_response).encode()
        return response

    return wrapper
