import math

from src.shared.helpers.functions.haversine import EARTH_RADIUS_KM, haversine_km


class TestHaversine:
    def test_zero_distance_for_same_point(self):
        assert haversine_km(-23.56, -46.65, -23.56, -46.65) == 0.0

    def test_known_distance_sao_paulo_to_rio(self):
        # São Paulo (-23.5505, -46.6333) → Rio (-22.9068, -43.1729) ≈ 360 km em linha reta.
        sp_lat, sp_lon = -23.5505, -46.6333
        rio_lat, rio_lon = -22.9068, -43.1729
        distance = haversine_km(sp_lat, sp_lon, rio_lat, rio_lon)
        assert 355.0 < distance < 365.0, f"esperado ~360 km, obtido {distance}"

    def test_symmetric(self):
        a = haversine_km(-23.56, -46.65, -22.91, -43.17)
        b = haversine_km(-22.91, -43.17, -23.56, -46.65)
        assert math.isclose(a, b)

    def test_antipodal_points_close_to_half_circumference(self):
        # Pontos antípodas devem distar ~π × R = ~20.015 km.
        distance = haversine_km(0.0, 0.0, 0.0, 180.0)
        expected = math.pi * EARTH_RADIUS_KM
        assert math.isclose(distance, expected, rel_tol=1e-6)
