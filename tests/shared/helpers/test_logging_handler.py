import json
import logging

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
