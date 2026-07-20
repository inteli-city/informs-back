import json
from decimal import Decimal
from json import JSONDecodeError
from typing import Any
from urllib.parse import parse_qs

from src.shared.helpers.external_interfaces.http_models import HttpRequest, HttpResponse

DEFAULT_LAMBDA_RESPONSE_BODY = {"message": "No response"}
DEFAULT_LAMBDA_RESPONSE_HEADERS = {"Content-Type": "application/json"}


class LambdaHttpResponse(HttpResponse):
    """
    A class to represent an HTTP response for lambda URL.
    docs: https://docs.aws.amazon.com/lambda/latest/dg/lambda-urls.html
    """

    status_code: int = 200
    body: Any = DEFAULT_LAMBDA_RESPONSE_BODY
    headers: dict = DEFAULT_LAMBDA_RESPONSE_HEADERS

    def __init__(self, body: Any = None, status_code: int = None, headers: dict = None, **kwargs) -> None:
        """
        Constructor for HttpResponse.
        Args:
            body: The body of the response. Can be a string or a dict.
            status_code: The status code of the response. Defaults to 200.
            headers: The headers of the response. Defaults to {"Content-Type": "application/json"}.
            **kwargs: Configuration of the HTTP response. Possible values: add_default_cors_headers (default is True)
        """

        resolved_body = body if body is not None else dict(DEFAULT_LAMBDA_RESPONSE_BODY)
        resolved_headers = dict(headers or DEFAULT_LAMBDA_RESPONSE_HEADERS)
        resolved_status_code = self.status_code if status_code is None else status_code

        if kwargs.get("add_default_cors_headers", True):
            resolved_headers["Access-Control-Allow-Origin"] = "*"

        super().__init__(body=resolved_body, headers=resolved_headers, status_code=resolved_status_code)

    def toDict(self) -> dict:
        """
        Returns a dict representation of the HttpResponse.
        Returns:
            {
                'statusCode': int,
                'body': str,
                'headers': dict,
                'isBase64Encoded': bool
            }
        """

        def _json_default(value):
            if isinstance(value, Decimal):
                return int(value) if value % 1 == 0 else float(value)
            raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")

        return {
            "statusCode": self.status_code,
            "body": json.dumps(self.body, default=_json_default),
            "headers": self.headers,
            "isBase64Encoded": False,
        }

    def __repr__(self):
        return (
            f"HttpResponse (status_code={self.status_code}, body={self.body}, headers={self.headers})"
        )


class LambdaDefaultHTTP:
    method: str = ""
    path: str = ""
    protocol: str = ""
    source_ip: str = ""
    user_agent: str = ""

    def __init__(self, data: dict = None) -> None:
        """
        Constructor for LambdaHttp.
        Args:
            event: dict - the event passed to the lambda function.
        """
        if not data:
            return
        self.method = data.get("method") or ""
        self.path = data.get("path") or ""
        self.protocol = data.get("protocol") or ""
        self.source_ip = data.get("sourceIp") or ""
        self.user_agent = data.get("userAgent") or ""

    def __eq__(self, other):
        if not isinstance(other, LambdaDefaultHTTP):
            return False
        return (
            self.method == other.method
            and self.path == other.path
            and self.protocol == other.protocol
            and self.source_ip == other.source_ip
            and self.user_agent == other.user_agent
        )


class LambdaHttpRequest(HttpRequest):
    """
    A class to represent an HTTP request for lambda URL.
    docs: https://docs.aws.amazon.com/lambda/latest/dg/lambda-urls.html
    """

    version: str
    raw_path: str
    raw_query_string: str
    headers: dict
    query_string_parameters: dict
    request_context: dict
    http: LambdaDefaultHTTP
    body: Any

    def __init__(self, data: dict = None) -> None:
        """
        Constructor for HttpResponse.
        """
        data = data or {}
        headers = data.get("headers")
        query_string_parameters = self._merge_query_params(data)

        path_parameters = data.get("pathParameters")
        body = None

        if "body" in data:
            try:
                body = json.loads(data.get("body"))
            except (JSONDecodeError, TypeError):
                body = data.get("body")

        super().__init__(body=body, headers=headers, query_params=query_string_parameters, path_params=path_parameters)

        self.version = data.get("version")
        self.raw_path = data.get("rawPath")
        self.raw_query_string = data.get("rawQueryString")
        self.query_string_parameters = data.get("queryStringParameters")
        self.request_context = data.get("requestContext")

        http_context = {}
        if self.request_context:
            http_context = (
                self.request_context.get("http")
                or self.request_context.get("external_interfaces")
                or {}
            )
        self.http = LambdaDefaultHTTP(http_context)

    @staticmethod
    def _merge_query_params(data: dict) -> dict:
        """Combina rawQueryString, multiValue e queryStringParameters numa fonte única.

        Precedência: rawQueryString > multiValueQueryStringParameters >
        queryStringParameters. Retorna o dict combinado, ou o
        queryStringParameters original quando nada foi combinado.
        """
        query_string_parameters = data.get("queryStringParameters")
        parsed_query_params = {}

        raw_query_string = data.get("rawQueryString") or ""
        if isinstance(raw_query_string, str) and raw_query_string:
            for key, values in parse_qs(raw_query_string, keep_blank_values=True).items():
                parsed_query_params[key] = values[0] if len(values) == 1 else values

        multi_value = data.get("multiValueQueryStringParameters")
        if isinstance(multi_value, dict):
            for key, values in multi_value.items():
                if key in parsed_query_params:
                    continue
                if isinstance(values, list) and len(values) == 1:
                    parsed_query_params[key] = values[0]
                else:
                    parsed_query_params[key] = values

        if isinstance(query_string_parameters, dict):
            for key, value in query_string_parameters.items():
                parsed_query_params.setdefault(key, value)

        return parsed_query_params if parsed_query_params else query_string_parameters


class HttpResponseRedirect(HttpResponse):
    def __init__(self, location: str) -> None:
        super().__init__(status_code=302, headers={"Location": location})
