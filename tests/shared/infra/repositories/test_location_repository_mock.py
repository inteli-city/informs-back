"""Testes do LocationRepositoryMock (interface ILocationRepository)."""

import pytest

from src.shared.domain.entities.location_ping import LocationPing
from src.shared.infra.repositories.location_repository_mock import (
    LocationRepositoryMock,
)


class TestLocationRepositoryMock:
    def test_returns_seeded_pings(self):
        repo = LocationRepositoryMock()
        pings = repo.query_history(
            user_id="fake-inspector-id", since_ms=0, until_ms=10_000
        )
        assert len(pings) == 5
        assert all(isinstance(p, LocationPing) for p in pings)
        assert all(p.user_id == "fake-inspector-id" for p in pings)

    def test_filters_by_user(self):
        repo = LocationRepositoryMock()
        pings = repo.query_history(user_id="other", since_ms=0, until_ms=10_000)
        assert pings == []

    def test_range_inclusive_on_both_ends(self):
        repo = LocationRepositoryMock()
        pings = repo.query_history(
            user_id="fake-inspector-id", since_ms=2000, until_ms=4000
        )
        assert [p.ts for p in pings] == [2000, 3000, 4000]

    def test_returns_chronological_order(self):
        repo = LocationRepositoryMock()
        pings = repo.query_history(
            user_id="fake-inspector-id", since_ms=0, until_ms=10_000
        )
        assert [p.ts for p in pings] == sorted(p.ts for p in pings)

    def test_lat_lng_are_floats(self):
        repo = LocationRepositoryMock()
        pings = repo.query_history(
            user_id="fake-inspector-id", since_ms=0, until_ms=10_000
        )
        assert pings[0].lat == pytest.approx(-23.5505)
        assert pings[0].lng == pytest.approx(-46.6333)
