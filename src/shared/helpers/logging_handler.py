import json
import logging
from functools import wraps
from json import JSONDecodeError
from typing import Any, Callable, Dict

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_logging_handler(fn: Callable[[Dict[str, Any], Any], Dict[str, Any]]):
    """
    Decorator responsável exclusivamente por logging no CloudWatch.
    Deve ser o decorator mais externo, acima do lambda_error_handler.

    - INFO:    requisição recebida e respostas 2xx/3xx
    - WARNING: respostas 4xx (erros de cliente)
    - ERROR:   respostas 5xx e exceções não tratadas (com traceback completo)
    """

    @wraps(fn)
    def wrapper(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        path = ""
        method = ""
        if isinstance(event, dict):
            path = event.get("rawPath") or event.get("path") or ""
            method = (
                event.get("requestContext", {}).get("http", {}).get("method")
                or event.get("httpMethod")
                or ""
            ).upper()

        logger.info("Requisição recebida: %s %s", method, path)

        try:
            response = fn(event, context)
        except Exception:
            logger.exception("Exceção não tratada em %s %s", method, path)
            raise

        status_code = response.get("statusCode") if isinstance(response, dict) else None

        if status_code is None or status_code < 400:
            logger.info("Resposta %s para %s %s", status_code, method, path)
        elif status_code < 500:
            error_name = _extract_error_name(response)
            logger.warning(
                "Erro de cliente %s em %s %s - %s",
                status_code,
                method,
                path,
                error_name,
            )
        else:
            error_name = _extract_error_name(response)
            logger.error(
                "Erro interno %s em %s %s - %s",
                status_code,
                method,
                path,
                error_name,
            )

        return response

    return wrapper


def _extract_error_name(response: dict) -> str:
    try:
        raw_body = response.get("body", "")
        parsed = json.loads(raw_body) if isinstance(raw_body, str) else raw_body
        if isinstance(parsed, dict):
            return parsed.get("error") or parsed.get("message", "")[:120]
    except (JSONDecodeError, TypeError):
        pass
    return ""
