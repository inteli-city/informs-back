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


class TestConnectionRegistryInspector:
    def test_register_returns_none_when_first(self):
        reg = ConnectionRegistry()
        ws = _ws()
        assert reg.register_inspector("u1", ws) is None
        assert ("u1", None) in reg.online_inspectors()

    def test_register_returns_previous_on_duplicate(self):
        reg = ConnectionRegistry()
        ws_old = _ws()
        ws_new = _ws()
        reg.register_inspector("u1", ws_old)
        previous = reg.register_inspector("u1", ws_new)
        assert previous is ws_old
        # nova substitui no registry
        assert len(reg.online_inspectors()) == 1

    def test_unregister_only_removes_matching_socket(self):
        reg = ConnectionRegistry()
        ws_old = _ws()
        ws_new = _ws()
        reg.register_inspector("u1", ws_old)
        reg.register_inspector("u1", ws_new)  # ws_old fica órfão
        # cleanup tardio do ws_old NÃO pode remover ws_new
        assert reg.unregister_inspector("u1", ws_old) is False
        assert len(reg.online_inspectors()) == 1
        assert reg.unregister_inspector("u1", ws_new) is True
        assert reg.online_inspectors() == []

    def test_update_last_known_persists(self):
        reg = ConnectionRegistry()
        reg.register_inspector("u1", _ws())
        loc = LocationOut(user_id="u1", lat=1, lng=2, ts=3, ts_device=4)
        reg.update_last_known("u1", loc)
        online = reg.online_inspectors()
        assert online[0][1] == loc

    def test_update_last_known_silent_for_unknown(self):
        reg = ConnectionRegistry()
        # não levanta — apenas no-op
        reg.update_last_known(
            "nope", LocationOut(user_id="nope", lat=0, lng=0, ts=1, ts_device=1)
        )
        assert reg.online_inspectors() == []

    def test_update_last_known_ignores_older_buffered_ping(self):
        """Cenário: app envia live ping primeiro, depois despeja buffered antigo.
        last_known deve continuar com o live (mais recente por ts_device)."""
        reg = ConnectionRegistry()
        reg.register_inspector("u1", _ws())

        live = LocationOut(user_id="u1", lat=10, lng=10, ts=2000, ts_device=1500)
        buffered_old = LocationOut(user_id="u1", lat=1, lng=1, ts=2001, ts_device=900)

        reg.update_last_known("u1", live)
        reg.update_last_known("u1", buffered_old)

        assert reg.online_inspectors()[0][1] == live

    def test_update_last_known_accepts_equal_ts_device(self):
        """Empate em ts_device atualiza (último ganha — sem regressão)."""
        reg = ConnectionRegistry()
        reg.register_inspector("u1", _ws())

        first = LocationOut(user_id="u1", lat=1, lng=1, ts=1000, ts_device=500)
        second = LocationOut(user_id="u1", lat=2, lng=2, ts=1001, ts_device=500)

        reg.update_last_known("u1", first)
        reg.update_last_known("u1", second)

        assert reg.online_inspectors()[0][1] == second

    def test_update_last_known_advances_with_newer_ping(self):
        reg = ConnectionRegistry()
        reg.register_inspector("u1", _ws())

        old = LocationOut(user_id="u1", lat=1, lng=1, ts=1000, ts_device=500)
        new = LocationOut(user_id="u1", lat=2, lng=2, ts=2000, ts_device=1500)

        reg.update_last_known("u1", old)
        reg.update_last_known("u1", new)

        assert reg.online_inspectors()[0][1] == new


class TestConnectionRegistryAdmin:
    def test_register_unregister(self):
        reg = ConnectionRegistry()
        ws = _ws()
        reg.register_admin(ws)
        assert ws in reg.admins()
        reg.unregister_admin(ws)
        assert ws not in reg.admins()

    def test_unregister_unknown_is_silent(self):
        reg = ConnectionRegistry()
        # discard não levanta
        reg.unregister_admin(_ws())

    def test_admines_returns_copy(self):
        reg = ConnectionRegistry()
        ws = _ws()
        reg.register_admin(ws)
        snap = reg.admins()
        reg.unregister_admin(ws)
        # snap continua com referência ao socket antigo (cópia rasa)
        assert ws in snap
