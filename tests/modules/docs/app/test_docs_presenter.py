import json
import os
import sys
from pathlib import Path

sys.path.append(os.getcwd())

from src.modules.docs.app import docs_presenter


def test_docs_presenter_success(monkeypatch):
    def fake_exists(self):
        return str(self).endswith("swagger.json")

    def fake_read_text(self, *args, **kwargs):
        if str(self).endswith("swagger.json"):
            return '{"openapi":"3.0.0","paths":{}}'
        raise FileNotFoundError

    monkeypatch.setattr(Path, "exists", fake_exists)
    monkeypatch.setattr(Path, "read_text", fake_read_text)

    response = docs_presenter.lambda_handler({}, None)

    assert response["statusCode"] == 200
    assert response["headers"]["Content-Type"] == "text/html"
    assert "SwaggerUIBundle" in response["body"]


def test_docs_presenter_file_not_found(monkeypatch):
    monkeypatch.setattr(Path, "exists", lambda *args, **kwargs: False)

    response = docs_presenter.lambda_handler({}, None)

    assert response["statusCode"] == 500
    assert "Swagger documentation not found" in response["body"]


def test_docs_presenter_unexpected_error(monkeypatch):
    def fake_exists(self):
        return str(self).endswith("swagger.json")

    def fake_read_text(*args, **kwargs):
        raise OSError("boom")

    monkeypatch.setattr(Path, "exists", fake_exists)
    monkeypatch.setattr(Path, "read_text", fake_read_text)

    response = docs_presenter.lambda_handler({}, None)
    body = json.loads(response["body"])

    assert response["statusCode"] == 500
    assert "Erro interno" in body["message"]
