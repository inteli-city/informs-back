import json
import os
import sys

sys.path.append(os.getcwd())

from src.shared.infra.repositories.origin_repository_apex import OriginRepositoryApex

UBERLANDIA_URL = (
    "https://g1a99674895752e-intelicitydataapex.adb.sa-saopaulo-1.oraclecloudapps.com"
    "/ords/supervisao/informs/cadastrar_formulario"
)


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


def _spy_urlopen(monkeypatch):
    calls = []

    def fake_urlopen(req, timeout):
        calls.append(req)
        return FakeResponse(200, '{"failed_form_ids":[]}')

    monkeypatch.setattr(
        "src.shared.infra.repositories.origin_repository_apex.urllib.request.urlopen",
        fake_urlopen,
    )
    return calls


def _send(repo, origin_system):
    return repo.sync_forms(
        origin_system=origin_system,
        payloads=[{"id": "form-1"}],
        execution_id="exec-u",
        logger=FakeLogger(),
    )


def test_uberlandia_usa_o_host_do_gaia_com_o_alias_supervisao(monkeypatch):
    calls = _spy_urlopen(monkeypatch)
    repo = OriginRepositoryApex()

    ok, status, _ = _send(repo, "uberlandia")

    assert (ok, status) == (True, 200)
    assert [req.full_url for req in calls] == [UBERLANDIA_URL]


def test_sobrescrita_por_variavel_troca_a_url_inteira(monkeypatch):
    calls = _spy_urlopen(monkeypatch)
    monkeypatch.setenv("APEX_URL_UBERLANDIA", "http://127.0.0.1:9999/fake/cadastrar")
    repo = OriginRepositoryApex()

    _send(repo, "uberlandia")

    assert [req.full_url for req in calls] == ["http://127.0.0.1:9999/fake/cadastrar"]


def test_origem_com_variavel_de_url_nao_afeta_as_outras(monkeypatch):
    calls = _spy_urlopen(monkeypatch)
    monkeypatch.setenv("APEX_URL_UBERLANDIA", "http://127.0.0.1:9999/fake/cadastrar")
    repo = OriginRepositoryApex()
    repo.sync_enabled = True

    _send(repo, "gaia")

    assert [req.full_url for req in calls] == [
        "https://g1a99674895752e-intelicitydataapex.adb.sa-saopaulo-1.oraclecloudapps.com"
        "/ords/gaia/informs/cadastrar_formulario"
    ]


def test_fora_de_prod_sem_lista_uberlandia_nao_envia(monkeypatch):
    calls = _spy_urlopen(monkeypatch)
    repo = OriginRepositoryApex()
    repo.sync_enabled = False
    repo.enabled_origins = frozenset()

    ok, status, body = _send(repo, "uberlandia")

    assert (ok, status, body) == (True, 200, "SKIPPED_NON_PROD")
    assert calls == []


def test_origem_listada_envia_fora_de_prod(monkeypatch):
    calls = _spy_urlopen(monkeypatch)
    repo = OriginRepositoryApex()
    repo.sync_enabled = False
    repo.enabled_origins = frozenset({"uberlandia"})

    ok, status, body = _send(repo, "uberlandia")

    assert (ok, status) == (True, 200)
    assert body != "SKIPPED_NON_PROD"
    assert [req.full_url for req in calls] == [UBERLANDIA_URL]


def test_listar_uberlandia_nao_liga_o_gaia(monkeypatch):
    calls = _spy_urlopen(monkeypatch)
    repo = OriginRepositoryApex()
    repo.sync_enabled = False
    repo.enabled_origins = frozenset({"uberlandia"})

    ok, status, body = _send(repo, "gaia")

    assert (ok, status, body) == (True, 200, "SKIPPED_NON_PROD")
    assert calls == []


def test_normalizacao_ignora_origem_desconhecida_e_registra_aviso(caplog):
    with caplog.at_level("WARNING"):
        enabled = OriginRepositoryApex._normalize_enabled_origins(("  Uberlandia ", "FOO", "gaia"))

    assert enabled == frozenset({"uberlandia", "gaia"})
    assert any("FOO" in record.getMessage() for record in caplog.records)


def test_payload_de_uberlandia_mantem_o_contrato(monkeypatch):
    calls = _spy_urlopen(monkeypatch)
    repo = OriginRepositoryApex()

    _send(repo, "uberlandia")

    body = json.loads(calls[0].data.decode("utf-8"))
    assert body == {"forms": [{"id": "form-1"}], "execution_id": "exec-u"}
