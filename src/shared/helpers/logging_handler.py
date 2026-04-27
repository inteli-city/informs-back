import logging
import traceback
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
            logger.error(
                "Exceção não tratada em %s %s\n%s",
                method,
                path,
                traceback.format_exc(),
            )
            raise

        status_code = response.get("statusCode") if isinstance(response, dict) else None

        if status_code is None or status_code < 400:
            logger.info("Resposta %s para %s %s", status_code, method, path)
        elif status_code < 500:
            body = response.get("body", "") if isinstance(response, dict) else ""
            logger.warning(
                "Erro de cliente %s em %s %s — %s",
                status_code,
                method,
                path,
                body,
            )
        else:
            body = response.get("body", "") if isinstance(response, dict) else ""
            logger.error(
                "Erro interno %s em %s %s — %s",
                status_code,
                method,
                path,
                body,
            )

        return response

    return wrapper
