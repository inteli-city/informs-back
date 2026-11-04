import json
import logging
import re

import pytest

from src.shared.helpers.logging_handler import lambda_logging_handler


def test_lambda_logging_handler_logs_error_name_without_response_body(caplog):
    response = {
        "statusCode": 403,
        "body": json.dumps({
            "error": "ForbiddenAction",
            "message": "full business message with internal detail",
        }),
    }

    @lambda_logging_handler
    def handler(event, context):
        return response

    caplog.set_level(logging.WARNING)
    returned = handler({
        "rawPath": "/forms/1",
        "requestContext": {"http": {"method": "POST"}},
    }, None)

    warning_messages = [record.getMessage() for record in caplog.records if record.levelno == logging.WARNING]

    assert returned is response
    assert any("ForbiddenAction" in message for message in warning_messages)
    assert all("full business message with internal detail" not in message for message in warning_messages)


def test_lambda_logging_handler_logs_and_reraises_unhandled_exception(caplog):
    @lambda_logging_handler
    def handler(event, context):
        raise RuntimeError("boom")

    caplog.set_level(logging.ERROR)

    with pytest.raises(RuntimeError, match="boom"):
        handler({
            "path": "/forms/1",
            "httpMethod": "DELETE",
        }, None)

    error_records = [record for record in caplog.records if record.levelno == logging.ERROR]

    # logger.exception anexa o traceback via exc_info (não no texto da mensagem).
    assert any(
        record.exc_info is not None and record.exc_info[0] is RuntimeError
        for record in error_records
    )
    assert "RuntimeError: boom" in caplog.text


def test_lambda_logging_handler_masks_search_and_logs_only_allowed_query_keys(caplog):
    @lambda_logging_handler
    def handler(event, context):
        return {"statusCode": 200}

    caplog.set_level(logging.INFO)
    handler({
        "rawPath": "/forms",
        "requestContext": {"http": {"method": "GET"}},
        "queryStringParameters": {"limit": "50", "scope": "pool", "search": "Fulano"},
    }, None)

    received = [record.getMessage() for record in caplog.records if "Requisição recebida" in record.getMessage()]

    assert len(received) == 1
    assert "limit=50" in received[0]
    assert "scope=pool" in received[0]
    assert "search=<informado>" in received[0]
    assert "Fulano" not in received[0]


def test_lambda_logging_handler_omits_query_summary_when_there_is_no_query(caplog):
    @lambda_logging_handler
    def handler(event, context):
        return {"statusCode": 200}

    caplog.set_level(logging.INFO)
    handler({
        "rawPath": "/forms",
        "requestContext": {"http": {"method": "GET"}},
    }, None)

    received = [record.getMessage() for record in caplog.records if "Requisição recebida" in record.getMessage()]

    assert len(received) == 1
    assert received[0] == "Requisição recebida: GET /forms"


# --- Telemetria: updated_after na entrada, duração e bytes na saída ----------

# Sufixo de toda linha de resposta: ` duracao_ms=<int> bytes=<int>`, no fim.
RESPONSE_SUFFIX = re.compile(r" duracao_ms=(\d+) bytes=(\d+)$")


def _messages(caplog, needle):
    return [record.getMessage() for record in caplog.records if needle in record.getMessage()]


def test_updated_after_numeric_is_logged_as_instant(caplog):
    @lambda_logging_handler
    def handler(event, context):
        return {"statusCode": 200}

    caplog.set_level(logging.INFO)
    handler({
        "rawPath": "/forms",
        "requestContext": {"http": {"method": "GET"}},
        "queryStringParameters": {"scope": "pool", "updated_after": "1730000000000"},
    }, None)

    received = _messages(caplog, "Requisição recebida")
    assert len(received) == 1
    assert "updated_after=1730000000000" in received[0]


def test_updated_after_non_numeric_is_logged_as_invalid(caplog):
    @lambda_logging_handler
    def handler(event, context):
        return {"statusCode": 200}

    caplog.set_level(logging.INFO)
    handler({
        "rawPath": "/forms",
        "requestContext": {"http": {"method": "GET"}},
        "queryStringParameters": {"updated_after": "abc"},
    }, None)

    received = _messages(caplog, "Requisição recebida")
    assert len(received) == 1
    assert "updated_after=<inválido>" in received[0]
    assert "abc" not in received[0]


def test_updated_after_with_sign_or_fraction_is_not_a_plain_instant(caplog):
    @lambda_logging_handler
    def handler(event, context):
        return {"statusCode": 200}

    caplog.set_level(logging.INFO)
    handler({
        "rawPath": "/forms",
        "requestContext": {"http": {"method": "GET"}},
        "queryStringParameters": {"updated_after": "-1730000000000.5"},
    }, None)

    received = _messages(caplog, "Requisição recebida")
    assert "updated_after=<inválido>" in received[0]


def test_updated_after_with_trailing_newline_is_not_logged_raw(caplog):
    @lambda_logging_handler
    def handler(event, context):
        return {"statusCode": 200}

    caplog.set_level(logging.INFO)
    handler({
        "rawPath": "/forms",
        "requestContext": {"http": {"method": "GET"}},
        "queryStringParameters": {"updated_after": "1730000000000\n"},
    }, None)

    received = _messages(caplog, "Requisição recebida")
    assert "updated_after=<inválido>" in received[0]
    assert "1730000000000" not in received[0]


def test_success_line_ends_with_duration_and_utf8_byte_count(caplog):
    body = json.dumps({"forms": [], "nota": "ação concluída"}, ensure_ascii=False)
    # Garante que o caso testa UTF-8: caracteres e bytes diferem.
    assert len(body) != len(body.encode("utf-8"))

    @lambda_logging_handler
    def handler(event, context):
        return {"statusCode": 200, "body": body}

    caplog.set_level(logging.INFO)
    handler({"rawPath": "/forms", "requestContext": {"http": {"method": "GET"}}}, None)

    received = _messages(caplog, "Resposta 200")
    assert len(received) == 1
    assert received[0].startswith("Resposta 200 para GET /forms")
    match = RESPONSE_SUFFIX.search(received[0])
    assert match is not None
    assert int(match.group(1)) >= 0
    assert int(match.group(2)) == len(body.encode("utf-8"))


def test_client_error_line_ends_with_duration_and_bytes(caplog):
    body = json.dumps({"error": "NotFound", "message": "não encontrado"}, ensure_ascii=False)

    @lambda_logging_handler
    def handler(event, context):
        return {"statusCode": 404, "body": body}

    caplog.set_level(logging.WARNING)
    handler({"rawPath": "/forms/1", "requestContext": {"http": {"method": "GET"}}}, None)

    received = _messages(caplog, "Erro de cliente 404")
    assert len(received) == 1
    assert received[0].startswith("Erro de cliente 404 em GET /forms/1 - NotFound")
    match = RESPONSE_SUFFIX.search(received[0])
    assert match is not None
    assert int(match.group(2)) == len(body.encode("utf-8"))


def test_server_error_line_ends_with_duration_and_bytes(caplog):
    body = json.dumps({"error": "InternalError"})

    @lambda_logging_handler
    def handler(event, context):
        return {"statusCode": 500, "body": body}

    caplog.set_level(logging.ERROR)
    handler({"rawPath": "/forms", "requestContext": {"http": {"method": "POST"}}}, None)

    received = _messages(caplog, "Erro interno 500")
    assert len(received) == 1
    assert received[0].startswith("Erro interno 500 em POST /forms - InternalError")
    match = RESPONSE_SUFFIX.search(received[0])
    assert match is not None
    assert int(match.group(2)) == len(body.encode("utf-8"))


def test_response_without_body_reports_zero_bytes(caplog):
    @lambda_logging_handler
    def handler(event, context):
        return {"statusCode": 204}

    caplog.set_level(logging.INFO)
    handler({"rawPath": "/forms/1", "requestContext": {"http": {"method": "DELETE"}}}, None)

    received = _messages(caplog, "Resposta 204")
    assert len(received) == 1
    match = RESPONSE_SUFFIX.search(received[0])
    assert match is not None
    assert int(match.group(2)) == 0


def test_unhandled_exception_line_gets_duration_and_reraises(caplog):
    @lambda_logging_handler
    def handler(event, context):
        raise RuntimeError("boom")

    caplog.set_level(logging.ERROR)
    with pytest.raises(RuntimeError, match="boom"):
        handler({"path": "/forms/1", "httpMethod": "DELETE"}, None)

    received = _messages(caplog, "Exceção não tratada")
    assert len(received) == 1
    assert received[0].startswith("Exceção não tratada em DELETE /forms/1")
    assert re.search(r" duracao_ms=\d+$", received[0]) is not None


def test_search_stays_masked_and_prefixes_are_kept(caplog):
    @lambda_logging_handler
    def handler(event, context):
        return {"statusCode": 200, "body": "{}"}

    caplog.set_level(logging.INFO)
    handler({
        "rawPath": "/forms",
        "requestContext": {"http": {"method": "GET"}},
        "queryStringParameters": {"search": "Fulano da Silva", "updated_after": "1730000000000"},
    }, None)

    entry = _messages(caplog, "Requisição recebida")[0]
    exit_line = _messages(caplog, "Resposta 200")[0]
    assert "search=<informado>" in entry
    for line in (entry, exit_line):
        assert "Fulano" not in line
    assert entry.startswith("Requisição recebida: GET /forms")
