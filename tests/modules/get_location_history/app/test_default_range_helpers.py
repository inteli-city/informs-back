"""Testes dos helpers _default_since_ms / _default_until_ms.

Garantem que o default 'rota do dia' usa America/Sao_Paulo (não UTC) —
relevante porque entre 21:00–23:59 BRT já é dia seguinte em UTC, e
o admin esperaria ver o que o inspector fez 'hoje' do ponto de vista local.
"""

from datetime import datetime, time
from zoneinfo import ZoneInfo

from src.modules.get_location_history.app.get_location_history_controller import (
    _default_since_ms,
    _default_until_ms,
    _OPERATION_TZ,
)


class TestDefaultRangeHelpers:
    def test_default_since_is_midnight_brt_today(self):
        since_ms = _default_since_ms()
        since_dt_utc = datetime.fromtimestamp(since_ms / 1000, tz=ZoneInfo("UTC"))
        since_dt_local = since_dt_utc.astimezone(_OPERATION_TZ)
        # Hora local deve ser exatamente 00:00:00.
        assert since_dt_local.time() == time.min
        # Data local deve ser hoje (em São Paulo).
        today_local = datetime.now(_OPERATION_TZ).date()
        assert since_dt_local.date() == today_local

    def test_default_until_is_close_to_now(self):
        before = int(datetime.now(ZoneInfo("UTC")).timestamp() * 1000)
        until_ms = _default_until_ms()
        after = int(datetime.now(ZoneInfo("UTC")).timestamp() * 1000)
        assert before <= until_ms <= after

    def test_since_is_before_until(self):
        assert _default_since_ms() < _default_until_ms()
