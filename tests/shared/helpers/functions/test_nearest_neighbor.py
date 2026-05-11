import math

import pytest

from src.shared.helpers.functions.nearest_neighbor import (
    order_by_nearest_neighbor,
    total_route_distance_km,
)


class TestOrderByNearestNeighbor:
    def test_empty_returns_empty(self):
        assert order_by_nearest_neighbor([], start=(0.0, 0.0)) == []

    def test_single_point_returns_itself(self):
        assert order_by_nearest_neighbor([(1.0, 1.0)], start=(0.0, 0.0)) == [0]

    def test_picks_nearest_point_first(self):
        # start está em (0,0); ponto 1 está MUITO mais perto que ponto 0.
        points = [(10.0, 10.0), (0.1, 0.1)]
        ordered = order_by_nearest_neighbor(points, start=(0.0, 0.0))
        assert ordered == [1, 0]

    def test_three_points_in_a_line(self):
        # start em (0,0); pontos a 1°, 2°, 3° de longitude.
        # Ordem esperada: 0 → 1 → 2 (sempre o próximo é o mais próximo).
        points = [(0.0, 1.0), (0.0, 2.0), (0.0, 3.0)]
        ordered = order_by_nearest_neighbor(points, start=(0.0, 0.0))
        assert ordered == [0, 1, 2]

    def test_returns_all_indices_exactly_once(self):
        # Validação geral: para qualquer entrada, retorna permutação completa.
        points = [(1.0, 1.0), (2.0, 2.0), (3.0, 3.0), (4.0, 4.0), (5.0, 5.0)]
        ordered = order_by_nearest_neighbor(points, start=(0.0, 0.0))
        assert sorted(ordered) == list(range(len(points)))


class TestTotalRouteDistanceKm:
    def test_empty_no_end_returns_zero(self):
        assert total_route_distance_km([], start=(0.0, 0.0)) == pytest.approx(0.0, abs=1e-9)

    def test_empty_with_end_returns_distance_start_to_end(self):
        # Sem pontos intermediários: total é só haversine(start, end).
        # São Paulo → Rio ≈ 360 km
        distance = total_route_distance_km(
            [], start=(-23.5505, -46.6333), end=(-22.9068, -43.1729)
        )
        assert 355.0 < distance < 365.0

    def test_open_route_does_not_include_end_segment(self):
        # Apenas start → único ponto, sem end.
        distance = total_route_distance_km(
            [(0.0, 1.0)], start=(0.0, 0.0)
        )
        # haversine de 1° de longitude no equador ≈ 111 km
        assert 110.0 < distance < 112.0

    def test_closed_route_includes_end_segment(self):
        # start (0,0) → ponto único (0,1) → volta pra (0,0).
        # 2 segmentos de ~111 km = ~222 km.
        distance = total_route_distance_km(
            [(0.0, 1.0)], start=(0.0, 0.0), end=(0.0, 0.0)
        )
        assert 220.0 < distance < 224.0

    def test_sums_all_consecutive_segments(self):
        # 3 pontos em linha reta no equador a 1°, 2°, 3° de longitude.
        # start→p1: 111 km, p1→p2: 111 km, p2→p3: 111 km. Total ≈ 333 km.
        distance = total_route_distance_km(
            [(0.0, 1.0), (0.0, 2.0), (0.0, 3.0)],
            start=(0.0, 0.0),
        )
        assert 330.0 < distance < 336.0
