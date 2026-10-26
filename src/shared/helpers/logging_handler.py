import json
import logging
from functools import wraps
from json import JSONDecodeError
from typing import Any, Callable, Dict
from urllib.parse import parse_qs

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Únicas chaves da query string que vão para o log: operacionais, sem dado
# pessoal. `search` pode conter nome de rua, CPF, etc. — dela se registra
# apenas a presença, nunca o texto buscado.
_QUERY_LOG_KEYS = ("limit", "scope", "system", "status")


def _query_string_summary(event: Dict[str, Any]) -> str:
    """Resumo da query string numa linha, já filtrado, para anexar ao log de
    entrada (ex.: ' limit=50 scope=pool search=<informado>')."""
    if not isinstance(event, dict):
        return ""

    params = event.get("queryStringParameters")
    if not isinstance(params, dict):
        raw = event.get("rawQueryString") or ""
        if not raw:
            return ""
        parsed = parse_qs(raw, keep_blank_values=True)
        params = {key: values[-1] for key, values in parsed.items() if values}

    parts = [f"{key}={params[key]}" for key in _QUERY_LOG_KEYS if params.get(key) is not None]
    if params.get("search") is not None:
        parts.append("search=<informado>")
    return f" {' '.join(parts)}" if parts else ""


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

        logger.info("Requisição recebida: %s %s%s", method, path, _query_string_summary(event))

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
