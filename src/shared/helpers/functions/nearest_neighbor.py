from typing import List, Optional, Tuple

from src.shared.helpers.functions.haversine import haversine_km


Coord = Tuple[float, float]  # (latitude, longitude)


def order_by_nearest_neighbor(
    points: List[Coord],
    start: Coord,
) -> List[int]:
    """
    Retorna uma permutação dos índices originais de `points` na ordem de
    visita escolhida pelo algoritmo nearest-neighbor (greedy).

    A partir de `start`, escolhe iterativamente o ponto não-visitado mais
    próximo (Haversine) e segue até esgotar a lista.

    Complexidade: O(n²). Para n até ~50 (limite do endpoint), é praticamente
    instantâneo. Não garante ordem ótima como TSP exato, mas costuma ficar
    a ~25% do ótimo — bom o suficiente para esta aplicação.
    """
    n = len(points)
    if n == 0:
        return []

    visited = [False] * n
    ordered_indices: List[int] = []
    current_lat, current_lon = start

    for _ in range(n):
        best_index = -1
        best_distance = float("inf")
        for i in range(n):
            if visited[i]:
                continue
            distance = haversine_km(current_lat, current_lon, points[i][0], points[i][1])
            if distance < best_distance:
                best_distance = distance
                best_index = i
        visited[best_index] = True
        ordered_indices.append(best_index)
        current_lat, current_lon = points[best_index]

    return ordered_indices


def total_route_distance_km(
    ordered_points: List[Coord],
    start: Coord,
    end: Optional[Coord] = None,
) -> float:
    """
    Calcula a distância total da rota:
      start -> ordered_points[0] -> ordered_points[1] -> ... -> ordered_points[-1] [-> end]

    Se `end` é None, a rota termina no último ponto (rota aberta) e não soma
    o trecho final.
    """
    if not ordered_points:
        if end is None:
            return 0.0
        return haversine_km(start[0], start[1], end[0], end[1])

    total = haversine_km(start[0], start[1], ordered_points[0][0], ordered_points[0][1])
    for i in range(len(ordered_points) - 1):
        total += haversine_km(
            ordered_points[i][0], ordered_points[i][1],
            ordered_points[i + 1][0], ordered_points[i + 1][1],
        )
    if end is not None:
        last_lat, last_lon = ordered_points[-1]
        total += haversine_km(last_lat, last_lon, end[0], end[1])
    return total
