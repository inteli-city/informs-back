import json
import logging
from datetime import datetime, timezone
from typing import Any, Callable, Dict

from src.shared.helpers.enum.http_status_code_enum import HttpStatusCodeEnum
from src.shared.helpers.errors.base_error import BaseError
from src.shared.helpers.errors.controller_errors import MissingParameters, WrongTypeParameter
from src.shared.helpers.errors.domain_errors import EntityError
from src.shared.helpers.errors.usecase_errors import DuplicatedItem, ForbiddenAction, NoItemsFound
from src.shared.helpers.external_interfaces.http_lambda_requests import LambdaHttpResponse

_logger = logging.getLogger(__name__)


def lambda_error_handler(fn: Callable[[Dict[str, Any], Any], Dict[str, Any]]):
    """
    Decorator to normalize errors raised inside Lambda presenters into a standard HTTP response payload.
    """

    def wrapper(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        try:
            resp = fn(event, context)
            return _normalize_response(resp, event)
        except NoItemsFound as err:
            return _make_response(HttpStatusCodeEnum.NOT_FOUND.value, err.message, "NoItemsFound", event)
        except ForbiddenAction as err:
            return _make_response(HttpStatusCodeEnum.FORBIDDEN.value, err.message, "ForbiddenAction", event)
        except DuplicatedItem as err:
            return _make_response(HttpStatusCodeEnum.CONFLICT.value, err.message, "DuplicatedItem", event)
        except (MissingParameters, WrongTypeParameter, EntityError, ValueError) as err:
            return _make_response(HttpStatusCodeEnum.BAD_REQUEST.value, str(err), err.__class__.__name__, event)
        except BaseError as err:
            return _make_response(HttpStatusCodeEnum.BAD_REQUEST.value, err.message, err.__class__.__name__, event)
        except Exception as err:
            _logger.exception("Unhandled exception: %s", err)
            return _make_response(HttpStatusCodeEnum.INTERNAL_SERVER_ERROR.value, "Erro interno do servidor", "InternalServerError", event)

    return wrapper


def _normalize_response(response: Dict[str, Any], event: Dict[str, Any]) -> Dict[str, Any]:
    """
    If a handler returns an error response (status >= 400), wrap it into the standardized structure.
    """
    if not isinstance(response, dict):
        return response

    status_code = response.get("statusCode")
    if status_code is None or status_code < 400:
        return response

    raw_body = response.get("body")
    message = ""
    error_name = "HttpError"

    try:
        parsed = json.loads(raw_body) if isinstance(raw_body, str) else raw_body
        if isinstance(parsed, dict):
            message = parsed.get("message") or parsed.get("error") or str(parsed)
            error_name = parsed.get("error") or error_name
        else:
            message = str(parsed)
    except Exception:
        message = str(raw_body)

    return _make_response(status_code, message, error_name, event)


def _make_response(status: int, message: str, error_name: str, event: Dict[str, Any]) -> Dict[str, Any]:
    path = ""
    if isinstance(event, dict):
        path = event.get("rawPath") or event.get("path") or ""

    body = {
        "error": error_name,
        "message": message,
        "statusCode": status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "path": path,
    }

    return LambdaHttpResponse(
        status_code=status,
        body=body,
        headers={"Content-Type": "application/json"}
    ).toDict()
