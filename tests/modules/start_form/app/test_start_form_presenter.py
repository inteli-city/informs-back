import json
import os
import sys

sys.path.append(os.getcwd())

from src.modules.start_form.app.start_form_presenter import lambda_handler


def test_start_form_presenter_error_payload():
    event = {
        "body": "{}",
        "headers": {},
        "queryStringParameters": {},
        "requestContext": {},
        "rawPath": "/forms/abc/start",
    }

    resp = lambda_handler(event, None)

    assert resp["statusCode"] == 400
    body = json.loads(resp["body"])
    assert body["error"] == "HttpError"
    assert "requester_user" in body["message"]
    assert body["statusCode"] == 400
    assert body["path"] == "/forms/abc/start"
