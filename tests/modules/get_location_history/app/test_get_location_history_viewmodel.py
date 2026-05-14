"""Testes do GetLocationHistoryViewmodel."""

import pytest

from src.modules.get_location_history.app.get_location_history_viewmodel import (
    GetLocationHistoryViewmodel,
)
from src.shared.domain.entities.location_ping import LocationPing


class TestGetLocationHistoryViewmodel:
    def test_empty_list(self):
        vm = GetLocationHistoryViewmodel(pings=[])
        d = vm.to_dict()
        assert d == {"items": [], "count": 0}

    def test_with_pings(self):
        pings = [
            LocationPing(
                user_id="u1", lat=-23.5, lng=-46.6, ts=1000, ts_device=950, accuracy=5.0
            ),
            LocationPing(
                user_id="u1", lat=-23.6, lng=-46.7, ts=2000, ts_device=1950
            ),
        ]
        vm = GetLocationHistoryViewmodel(pings=pings)
        d = vm.to_dict()
        assert d["count"] == 2
        assert d["items"][0]["user_id"] == "u1"
        assert d["items"][0]["lat"] == pytest.approx(-23.5)
        assert d["items"][0]["accuracy"] == pytest.approx(5.0)
        assert d["items"][1]["accuracy"] is None
        assert d["items"][1]["ts"] == 2000
