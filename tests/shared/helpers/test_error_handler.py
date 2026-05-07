import json

from src.shared.helpers.error_handler import lambda_error_handler


def test_lambda_error_handler_returns_generic_internal_error_response():
    @lambda_error_handler
    def handler(event, context):
        raise RuntimeError("database password leaked")

    response = handler({"rawPath": "/forms"}, None)
    body = json.loads(response["body"])

    assert response["statusCode"] == 500
    assert body["error"] == "InternalServerError"
    assert body["message"] == "Erro interno do servidor"
    assert body["path"] == "/forms"
    assert "database password leaked" not in response["body"]


def test_lambda_error_handler_normalizes_returned_error_response():
    @lambda_error_handler
    def handler(event, context):
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "InvalidRequest", "message": "bad input"}),
        }

    response = handler({"path": "/templates"}, None)
    body = json.loads(response["body"])

    assert response["statusCode"] == 400
    assert body["error"] == "InvalidRequest"
    assert body["message"] == "bad input"
    assert body["path"] == "/templates"
