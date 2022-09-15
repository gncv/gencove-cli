"""Test decorators."""

import json
import os
from functools import wraps

import requests


def parse_response_to_json(func):
    """Decorator that parses the response body into JSON and passes it to the
    function, then it saves the changes into the response body again.
    """

    @wraps(func)
    def wrapper(response):
        try:
            json_response = json.loads(response["body"]["string"])
        except (json.decoder.JSONDecodeError, UnicodeDecodeError):
            json_response = {}
        response, json_response = func(response, json_response)
        if response is not None and json_response:
            response["body"]["string"] = json.dumps(json_response).encode()
        return response

    return wrapper


def assert_authorization(func):
    """Decorator that ensures that the API key is being passed to our
    endpoints, and the login endpoint is called if email/password is provided.
    """

    @wraps(func)
    def wrapper(*args, mocker, **kwargs):
        host = os.getenv("GENCOVE_HOST")
        api_key = os.getenv("GENCOVE_API_KEY_TEST")
        email = os.getenv("GENCOVE_EMAIL_TEST")
        password = os.getenv("GENCOVE_PASSWORD_TEST")
        using_api_key = os.getenv("USING_API_KEY")

        def mock_get_auth(url, *args, headers, **kwargs):
            if host in url and using_api_key:
                assert (
                    headers["Authorization"] == f"Api-Key {api_key}"
                ), f"No valid authorization header provided for GET-{url}"
            kwargs["headers"] = headers
            return requests.get(url, *args, **kwargs)

        mocker.patch("gencove.client.get", side_effect=mock_get_auth)
        login_called = False

        def mock_post_auth(url, data, *args, headers, **kwargs):
            nonlocal login_called
            if host in url and using_api_key:
                assert (
                    headers["Authorization"] == f"Api-Key {api_key}"
                ), f"No valid authorization header provided for POST-{url}"
            elif host in url:
                if url.endswith("jwt-create/"):
                    login_called = True
                    data_json = json.loads(data)
                    assert data_json["email"] == email
                    assert data_json["password"] == password
                else:
                    assert "Bearer " in headers.get("Authorization")
            kwargs["headers"] = headers
            return requests.post(url, data, *args, **kwargs)

        mocker.patch("gencove.client.post", side_effect=mock_post_auth)
        kwargs["mocker"] = mocker
        func(*args, **kwargs)
        if not using_api_key:
            assert login_called, "jwt-create endpoint was not called"

    return wrapper


def assert_no_requests(func):
    """Decorator that mocks get, post and delete and asserts that
    none of those methods are called
    """

    @wraps(func)
    def wrapper(*args, mocker, **kwargs):
        mock_get = mocker.patch("gencove.client.get")
        mock_post = mocker.patch("gencove.client.post")
        mock_delete = mocker.patch("gencove.client.delete")

        kwargs["mocker"] = mocker
        func(*args, **kwargs)

        mock_get.assert_not_called()
        mock_post.assert_not_called()
        mock_delete.assert_not_called()

    return wrapper
