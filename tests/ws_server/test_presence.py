"""Tests do ConnectionRegistry — sem rede, com WebSocket falso."""

from typing import cast
from unittest.mock import MagicMock

from fastapi import WebSocket

from ws_server.messages import LocationOut
from ws_server.presence import ConnectionRegistry


def _ws() -> WebSocket:
    """Stub mínimo: o registry só compara identidade dos sockets.

    Casting pra WebSocket silencia python:S5655 (type checker do Sonar)
    sem incorrer em deps reais — MagicMock(spec=WebSocket) atende ao
    contrato estrutural do que o registry usa.
    """
    return cast(WebSocket, MagicMock(spec=WebSocket))


class TestConnectionRegistryMotoca:
    def test_register_returns_none_when_first(self):
        reg = ConnectionRegistry()
        ws = _ws()
        assert reg.register_motoca("u1", ws) is None
        assert ("u1", None) in reg.online_motocas()

    def test_register_returns_previous_on_duplicate(self):
        reg = ConnectionRegistry()
        ws_old = _ws()
        ws_new = _ws()
        reg.register_motoca("u1", ws_old)
        previous = reg.register_motoca("u1", ws_new)
        assert previous is ws_old
        # nova substitui no registry
        assert len(reg.online_motocas()) == 1

    def test_unregister_only_removes_matching_socket(self):
        reg = ConnectionRegistry()
        ws_old = _ws()
        ws_new = _ws()
        reg.register_motoca("u1", ws_old)
        reg.register_motoca("u1", ws_new)  # ws_old fica órfão
        # cleanup tardio do ws_old NÃO pode remover ws_new
        assert reg.unregister_motoca("u1", ws_old) is False
        assert len(reg.online_motocas()) == 1
        assert reg.unregister_motoca("u1", ws_new) is True
        assert reg.online_motocas() == []

    def test_update_last_known_persists(self):
        reg = ConnectionRegistry()
        reg.register_motoca("u1", _ws())
        loc = LocationOut(user_id="u1", lat=1, lng=2, ts=3, ts_device=4)
        reg.update_last_known("u1", loc)
        online = reg.online_motocas()
        assert online[0][1] == loc

    def test_update_last_known_silent_for_unknown(self):
        reg = ConnectionRegistry()
        # não levanta — apenas no-op
        reg.update_last_known(
            "nope", LocationOut(user_id="nope", lat=0, lng=0, ts=1, ts_device=1)
        )
        assert reg.online_motocas() == []


class TestConnectionRegistryGestor:
    def test_register_unregister(self):
        reg = ConnectionRegistry()
        ws = _ws()
        reg.register_gestor(ws)
        assert ws in reg.gestores()
        reg.unregister_gestor(ws)
        assert ws not in reg.gestores()

    def test_unregister_unknown_is_silent(self):
        reg = ConnectionRegistry()
        # discard não levanta
        reg.unregister_gestor(_ws())

    def test_gestores_returns_copy(self):
        reg = ConnectionRegistry()
        ws = _ws()
        reg.register_gestor(ws)
        snap = reg.gestores()
        reg.unregister_gestor(ws)
        # snap continua com referência ao socket antigo (cópia rasa)
        assert ws in snap
