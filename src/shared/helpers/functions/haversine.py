from math import asin, cos, radians, sin, sqrt


EARTH_RADIUS_KM = 6371.0


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calcula a distância em quilômetros (linha reta sobre a esfera) entre dois
    pontos lat/lon usando a fórmula de Haversine.

    Não considera trânsito real — para isso seria preciso integrar um serviço
    de roteamento (Google/Mapbox). Para planejamento de rota com poucos
    pontos (até dezenas), Haversine é mais que suficiente como heurística.
    """
    lat1_rad = radians(lat1)
    lat2_rad = radians(lat2)
    delta_lat = radians(lat2 - lat1)
    delta_lon = radians(lon2 - lon1)

    a = sin(delta_lat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lon / 2) ** 2
    c = 2 * asin(sqrt(a))

    return EARTH_RADIUS_KM * c
