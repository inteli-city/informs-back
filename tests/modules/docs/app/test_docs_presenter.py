import builtins
import io
import json
import os
import sys

sys.path.append(os.getcwd())

from src.modules.docs.app import docs_presenter


def test_docs_presenter_success(monkeypatch):
    def fake_open(path, mode="r"):
        assert path == "swagger.json"
        return io.StringIO("{}")

    monkeypatch.setattr(builtins, "open", fake_open)

    response = docs_presenter.lambda_handler({}, None)

    assert response["statusCode"] == 200
    assert response["headers"]["Content-Type"] == "text/html"
    assert "SwaggerUIBundle" in response["body"]


def test_docs_presenter_file_not_found(monkeypatch):
    def fake_open(*args, **kwargs):
        raise FileNotFoundError

    monkeypatch.setattr(builtins, "open", fake_open)

    response = docs_presenter.lambda_handler({}, None)

    assert response["statusCode"] == 500
    assert "Swagger documentation not found" in response["body"]


def test_docs_presenter_unexpected_error(monkeypatch):
    def fake_open(*args, **kwargs):
        raise OSError("boom")

    monkeypatch.setattr(builtins, "open", fake_open)

    response = docs_presenter.lambda_handler({}, None)
    body = json.loads(response["body"])

    assert response["statusCode"] == 500
    assert "Erro interno" in body["message"]
