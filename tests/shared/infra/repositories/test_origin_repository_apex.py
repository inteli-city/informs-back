import io
import os
import sys
import urllib.error

sys.path.append(os.getcwd())

from src.shared.infra.repositories.origin_repository_apex import OriginRepositoryApex


class FakeLogger:
    def __init__(self):
        self.events = []

    def info(self, message, extra=None):
        self.events.append(("info", message, extra or {}))

    def warning(self, message, extra=None):
        self.events.append(("warning", message, extra or {}))

    def error(self, message, extra=None):
        self.events.append(("error", message, extra or {}))


class FakeResponse:
    def __init__(self, status: int, body: str):
        self._status = status
        self._body = body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def getcode(self):
        return self._status

    def read(self):
        return self._body.encode("utf-8")


def test_origin_repository_apex_sync_forms_200_success(monkeypatch):
    calls = []

    def fake_urlopen(req, timeout):
        calls.append((req, timeout))
        return FakeResponse(200, '{"failed_form_ids":[]}')

    monkeypatch.setattr(
        "src.shared.infra.repositories.origin_repository_apex.urllib.request.urlopen",
        fake_urlopen,
    )

    repo = OriginRepositoryApex()
    logger = FakeLogger()

    ok, status, body = repo.sync_forms(
        origin_system="gaia",
        payloads=[{"id": "form-1"}],
        execution_id="exec-1",
        logger=logger,
    )

    assert ok is True
    assert status == 200
    assert "failed_form_ids" in body
    assert len(calls) == 1
    request, timeout = calls[0]
    assert timeout == repo.timeout
    assert request.full_url == (
        "https://g1a99674895752e-intelicitydataapex.adb.sa-saopaulo-1.oraclecloudapps.com"
        "/ords/gaia/informs/cadastrar_formulario"
    )
    assert any(event[1] == "origin request started" for event in logger.events)
    assert any(event[1] == "origin request completed" for event in logger.events)


def test_origin_repository_apex_sync_forms_202_is_failure(monkeypatch):
    calls = []

    def fake_urlopen(req, timeout):
        calls.append((req, timeout))
        return FakeResponse(202, '{"message":"accepted"}')

    monkeypatch.setattr(
        "src.shared.infra.repositories.origin_repository_apex.urllib.request.urlopen",
        fake_urlopen,
    )

    repo = OriginRepositoryApex()
    ok, status, body = repo.sync_forms(
        origin_system="gaia",
        payloads=[{"id": "form-1"}],
        execution_id="exec-1",
        logger=FakeLogger(),
    )

    assert ok is False
    assert status == 202
    assert "accepted" in body
    assert len(calls) == 1


def test_origin_repository_apex_sync_forms_http_error_returns_status_and_body(monkeypatch):
    calls = []

    def fake_urlopen(req, timeout):
        calls.append((req, timeout))
        raise urllib.error.HTTPError(
            url=req.full_url,
            code=500,
            msg="Internal Server Error",
            hdrs=None,
            fp=io.BytesIO(b'{"error":"DATABASE_ERROR"}'),
        )

    monkeypatch.setattr(
        "src.shared.infra.repositories.origin_repository_apex.urllib.request.urlopen",
        fake_urlopen,
    )

    repo = OriginRepositoryApex()
    ok, status, body = repo.sync_forms(
        origin_system="gaia",
        payloads=[{"id": "form-1"}],
        execution_id="exec-1",
        logger=FakeLogger(),
    )

    assert ok is False
    assert status == 500
    assert "DATABASE_ERROR" in body
    assert len(calls) == 1


def test_origin_repository_apex_sync_forms_connection_error_no_retry(monkeypatch):
    calls = []

    def fake_urlopen(req, timeout):
        calls.append((req, timeout))
        raise urllib.error.URLError("unreachable")

    monkeypatch.setattr(
        "src.shared.infra.repositories.origin_repository_apex.urllib.request.urlopen",
        fake_urlopen,
    )

    repo = OriginRepositoryApex()
    ok, status, body = repo.sync_forms(
        origin_system="gaia",
        payloads=[{"id": "form-1"}],
        execution_id="exec-1",
        logger=FakeLogger(),
    )

    assert ok is False
    assert status == 0
    assert "unreachable" in body
    assert len(calls) == 1


def test_origin_repository_apex_sync_forms_servicos_poa_keeps_default_host(monkeypatch):
    calls = []

    def fake_urlopen(req, timeout):
        calls.append((req, timeout))
        return FakeResponse(200, '{"failed_form_ids":[]}')

    monkeypatch.setattr(
        "src.shared.infra.repositories.origin_repository_apex.urllib.request.urlopen",
        fake_urlopen,
    )

    repo = OriginRepositoryApex()
    ok, status, body = repo.sync_forms(
        origin_system="servicos_poa",
        payloads=[{"id": "form-1"}],
        execution_id="exec-2",
        logger=FakeLogger(),
    )

    assert ok is True
    assert status == 200
    assert "failed_form_ids" in body
    assert len(calls) == 1
    request, timeout = calls[0]
    assert timeout == repo.timeout
    assert request.full_url == (
        "https://g1a99674895752e-intelicity.adb.sa-saopaulo-1.oraclecloudapps.com"
        "/ords/servicos_poa/informs/cadastrar_formulario"
    )
