"""Tests do schema do protocolo WS — bordas de validação dos pings."""

import pytest
from pydantic import ValidationError

from ws_server.messages import LocationOut, LocationPing, OnlineEntry, Snapshot


class TestLocationPing:
    def test_minimal_valid(self):
        ping = LocationPing(lat=-23.5, lng=-46.6, ts_device=1715000000000)
        assert ping.accuracy is None
        assert ping.lat == pytest.approx(-23.5)

    def test_with_accuracy(self):
        ping = LocationPing(lat=0, lng=0, ts_device=1, accuracy=5.5)
        assert ping.accuracy == pytest.approx(5.5)

    @pytest.mark.parametrize("lat,lng", [(-91, 0), (91, 0), (0, -181), (0, 181)])
    def test_out_of_range_coords_rejected(self, lat, lng):
        with pytest.raises(ValidationError):
            LocationPing(lat=lat, lng=lng, ts_device=1)

    def test_negative_ts_rejected(self):
        with pytest.raises(ValidationError):
            LocationPing(lat=0, lng=0, ts_device=0)

    def test_negative_accuracy_rejected(self):
        with pytest.raises(ValidationError):
            LocationPing(lat=0, lng=0, ts_device=1, accuracy=-0.1)


class TestSnapshot:
    def test_empty_online(self):
        s = Snapshot(online=[])
        d = s.model_dump()
        assert d["type"] == "snapshot"
        assert d["online"] == []

    def test_with_motocas(self):
        loc = LocationOut(
            user_id="u1", lat=0, lng=0, ts=1, ts_device=1, accuracy=None
        )
        s = Snapshot(online=[OnlineEntry(user_id="u1", last=loc)])
        d = s.model_dump()
        assert d["online"][0]["user_id"] == "u1"
        assert d["online"][0]["last"]["type"] == "location"
