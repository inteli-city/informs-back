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

    error_messages = [record.getMessage() for record in caplog.records if record.levelno == logging.ERROR]

    assert any("RuntimeError: boom" in message for message in error_messages)
