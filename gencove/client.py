"""Gencove API client.

Exclude imports from linters due to install aliases breaking the rules.
"""

# noqa Python 2 and 3 compatibility
# pylint: disable=wrong-import-order,wrong-import-position
from builtins import str as text  # noqa
import datetime  # noqa
import json  # noqa

try:
    # python 3
    from urllib.parse import urljoin, urlparse, parse_qs  # noqa
except ImportError:  # noqa
    # python 2.7
    from urlparse import urljoin, urlparse, parse_qs  # noqa

from requests import get, post, ConnectTimeout, ReadTimeout, codes  # noqa

from gencove import constants  # noqa: I100
from gencove.constants import SAMPLE_ASSIGNMENT_STATUS
from gencove.logger import echo_debug


class DateTimeEncoder(json.JSONEncoder):
    """JSON encoder that knows how to encode datetime objects."""

    # pylint: disable=method-hidden
    def default(self, o):
        """Override default method of JSONEncoder."""
        if isinstance(o, datetime.datetime):
            return o.isoformat()
        return json.JSONEncoder.default(self, o)


class APIError(Exception):
    """Base API Error."""

    def __init__(self, message):
        super(APIError, self).__init__(message)
        self.message = message


class APIClientError(APIError):
    """Base HTTP error."""


class APIClientTimeout(APIClientError):
    """API timeout exception.

    From http://docs.python-requests.org/en/master/user/quickstart/#timeouts

        timeout is not a time limit on the entire response download;
        rather, an exception is raised if the server
        has not issued a response for timeout seconds
        (more precisely, if no bytes have been received on the underlying
        socket for timeout seconds).
        If no timeout is specified explicitly, requests do not time out.

    Catching this error will catch both
    :exc:`~requests.exceptions.ConnectTimeout` and
    :exc:`~requests.exceptions.ReadTimeout` errors.

    ConnectTimeout:
        The request timed out while trying to connect to the remote server.
        Requests that produced this error are safe to retry.

    ReadTimeout:
        The server did not send any data in the allotted amount of time.
    """


class APIClient:
    """Gencove API client."""

    endpoints = constants.API_ENDPOINTS

    def __init__(self, host=None):
        """Initialize api client."""
        self._jwt_token = None
        self._jwt_refresh_token = None
        self._api_key = None
        self.host = host if host is not None else constants.HOST

    @staticmethod
    def _serialize_post_payload(payload):
        return json.dumps(payload, cls=DateTimeEncoder)

    # pylint: disable=too-many-arguments,bad-continuation
    def _request(
        self,
        endpoint="",
        params=None,
        method="get",
        custom_headers=None,
        timeout=60,
        sensitive=False,
    ):
        url = urljoin(text(self.host), text(endpoint))
        headers = {"content-type": "application/json", "date": None}
        if custom_headers:
            headers.update(custom_headers)

        if not params:
            params = {}

        echo_debug(
            "Contacting url: {} with payload: {}".format(
                url, "[SENSITIVE CONTENT]" if sensitive else params
            )
        )

        try:
            if method == "get":
                response = get(
                    url=url, params=params, headers=headers, timeout=timeout
                )
            else:
                post_payload = APIClient._serialize_post_payload(params)
                response = post(
                    url=url,
                    data=post_payload,
                    headers=headers,
                    timeout=timeout,
                )
        except ConnectTimeout:
            # If request timed out,
            # let upper level handle it they way it sees fit.
            # one place might want to retry another might not.
            raise APIClientTimeout("Could not connect to the api server")
        except ReadTimeout:
            raise APIClientTimeout(
                "API server did not respond in timely manner"
            )

        echo_debug(
            "API response is {} status is {}".format(
                "[SENSITIVE CONTENT]" if sensitive else response.content,
                response.status_code,
            )
        )

        # pylint: disable=no-member
        if (
            response.status_code == codes.ok
            or response.status_code == codes.created
        ):
            return response.json() if response.text else {}

        http_error_msg = ""
        if 400 <= response.status_code < 500:
            http_error_msg = "API Client Error: {}".format(response.reason)
            if response.text:
                response_json = response.json()
                if "detail" in response_json:
                    http_error_msg += ": {}".format(response_json["detail"])

        elif 500 <= response.status_code < 600:
            http_error_msg = "Server Error: {}".format(response.reason)

        raise APIClientError(http_error_msg)

    def _set_jwt(self, access_token, refresh_token=None):
        self._jwt_token = access_token
        if refresh_token is not None:
            self._jwt_refresh_token = refresh_token

    def _get_authorization(self):
        if self._api_key:
            return {"Authorization": "Api-Key {}".format(self._api_key)}

        try:
            self.validate_token(self._jwt_token)
        except APIClientError:
            jwt = self.refresh_token(self._jwt_refresh_token)
            self._set_jwt(jwt["access"])

        return {"Authorization": "Bearer {}".format(self._jwt_token)}

    def _post(
        self,
        endpoint,
        payload=None,
        timeout=120,
        authorized=False,
        sensitive=False,
    ):
        headers = {} if not authorized else self._get_authorization()
        return self._request(
            endpoint,
            params=payload,
            method="post",
            timeout=timeout,
            custom_headers=headers,
            sensitive=sensitive,
        )

    def _get(
        self,
        endpoint,
        query_params=None,
        timeout=120,
        authorized=False,
        sensitive=False,
    ):
        headers = {} if not authorized else self._get_authorization()
        return self._request(
            endpoint,
            params=query_params,
            method="get",
            timeout=timeout,
            custom_headers=headers,
            sensitive=sensitive,
        )

    @staticmethod
    def _add_query_params(next_link, query_params=None):
        if not query_params:
            query_params = {}
        query_params.update({"offset": 0, "limit": 200})
        if next_link:
            query_params["offset"] = parse_qs(urlparse(next_link).query)[
                "offset"
            ]
        return query_params

    def set_api_key(self, api_key):
        """Set api key on this instance."""
        self._api_key = api_key

    def refresh_token(self, refresh_token):
        """Refresh jwt token."""
        return self._post(
            self.endpoints.refresh_jwt,
            {"refresh": refresh_token},
            sensitive=True,
        )

    def validate_token(self, token):
        """Validate jwt token."""
        return self._post(
            self.endpoints.verify_jwt, {"token": token}, sensitive=True
        )

    def get_jwt(self, email, password):
        """Get jwt token."""
        return self._post(
            self.endpoints.get_jwt,
            dict(email=email, password=password),
            sensitive=True,
        )

    def login(self, email, password):
        """Log user in."""
        jwt = self.get_jwt(email, password)
        self._set_jwt(jwt["access"], jwt["refresh"])

    def get_upload_details(self, gncv_file_path, extra_params=None):
        """Get file upload details.
        Args:
            gncv_file_path (str): gncv notated path
            extra_params (dict): fastq sample mapping
                {
                    'batch'<str>: <batch id>,
                    'client_id'<str>: <sample client id>,
                    'r_notation'<str>: <one of r1 or r2>
                }

        Returns:
            dict: Upload details from the backend
        """
        payload = dict(destination_path=gncv_file_path)
        if extra_params:
            payload.update(extra_params)
        return self._post(
            self.endpoints.upload_details, payload, authorized=True
        )

    def get_upload_credentials(self):
        """Get aws credentials for user."""
        return self._post(
            self.endpoints.get_upload_credentials,
            authorized=True,
            sensitive=True,
        )

    def get_project_samples(self, project_id, next_link=None):
        """List single project's associated samples."""
        project_endpoint = self.endpoints.project_samples.format(
            id=project_id
        )
        params = self._add_query_params(next_link)
        return self._get(
            project_endpoint, query_params=params, authorized=True
        )

    def add_samples_to_project(self, samples, project_id):
        """Assign samples to a project.

        Args:
            samples (list of dicts): sample sheet results
            project_id (str): project to which to assign the samples
        """
        return self._post(
            self.endpoints.project_samples.format(id=project_id),
            samples,
            authorized=True,
        )

    def get_sample_details(self, sample_id):
        """Fetch single sample details."""
        return self._get(
            self.endpoints.sample_details.format(id=sample_id),
            authorized=True,
        )

    def get_sample_sheet(
        self,
        gncv_path=None,
        is_assigned=SAMPLE_ASSIGNMENT_STATUS.all,
        next_link=None,
    ):
        """Fetch user samples.

        Args:
            gncv_path (str): filter samples by gncv notated path.
            is_assigned (str, optional, default 'all'): filter samples by
                assignment status. One of SAMPLE_ASSIGNMENT_STATUS.
            next_link (str, optional): url from previous
                response['meta']['next'].
        """
        params = self._add_query_params(
            next_link, {"search": gncv_path, "status": is_assigned}
        )
        return self._get(
            self.endpoints.sample_sheet, query_params=params, authorized=True
        )
