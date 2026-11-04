import json
import logging
import re
import time
from functools import wraps
from json import JSONDecodeError
from typing import Any, Callable, Dict
from urllib.parse import parse_qs

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Únicas chaves da query string que vão para o log: operacionais, sem dado
# pessoal. `search` pode conter nome de rua, CPF, etc. — dela se registra
# apenas a presença, nunca o texto buscado.
# `updated_after` é um instante (epoch ms): sem ele, um refresh incremental
# parece carga completa nos logs. Só o valor numérico vai (ver _query_string_summary).
_QUERY_LOG_KEYS = ("limit", "scope", "system", "status", "updated_after")

# Instante em epoch ms: só dígitos. Qualquer outra coisa não entra no log.
_INSTANT_PATTERN = re.compile(r"^[0-9]+$")


def _query_part(key: str, value: Any) -> str:
    """Um par `chave=valor` do resumo. `updated_after` só vai se for um instante
    de dígitos; o resto vira `<inválido>` para não expor valor inesperado."""
    if key == "updated_after" and not _INSTANT_PATTERN.fullmatch(str(value)):
        return f"{key}=<inválido>"
    return f"{key}={value}"


def _duration_ms(started_at: float) -> int:
    """Tempo decorrido desde `started_at` (perf_counter), em ms inteiros."""
    return int((time.perf_counter() - started_at) * 1000)


def _body_bytes(response: Any) -> int:
    """Tamanho do corpo em bytes UTF-8. Não faz parse do corpo: ele pode ter
    centenas de KB e o log não precisa do conteúdo, só do tamanho."""
    if not isinstance(response, dict):
        return 0
    body = response.get("body")
    return len(body.encode("utf-8")) if isinstance(body, str) else 0


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

    parts = [_query_part(key, params[key]) for key in _QUERY_LOG_KEYS if params.get(key) is not None]
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
        started_at = time.perf_counter()
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
            # Sem resposta não há corpo: a linha de exceção leva só a duração.
            logger.exception(
                "Exceção não tratada em %s %s duracao_ms=%s",
                method,
                path,
                _duration_ms(started_at),
            )
            raise

        status_code = response.get("statusCode") if isinstance(response, dict) else None
        # Sufixo comum às linhas de resposta: acrescentado no fim, para não mudar
        # o prefixo que filtros e alarmes podem casar.
        timing = f" duracao_ms={_duration_ms(started_at)} bytes={_body_bytes(response)}"

        if status_code is None or status_code < 400:
            logger.info("Resposta %s para %s %s%s", status_code, method, path, timing)
        elif status_code < 500:
            error_name = _extract_error_name(response)
            logger.warning(
                "Erro de cliente %s em %s %s - %s%s",
                status_code,
                method,
                path,
                error_name,
                timing,
            )
        else:
            error_name = _extract_error_name(response)
            logger.error(
                "Erro interno %s em %s %s - %s%s",
                status_code,
                method,
                path,
                error_name,
                timing,
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
