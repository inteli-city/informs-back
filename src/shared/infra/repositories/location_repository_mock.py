"""Mock do ILocationRepository — lista em memória pré-populada.

Usado em testes (STAGE=TEST) e DOTENV. Imita o comportamento do
LocationRepositoryDynamo (filter por user_id + range de ts, ordenado
ascendente).
"""

from typing import List

from src.shared.domain.entities.location_ping import LocationPing
from src.shared.domain.repositories.location_repository_interface import (
    ILocationRepository,
)


class LocationRepositoryMock(ILocationRepository):
    def __init__(self):
        # Dataset mínimo pra testes: 5 pings de um inspector "fake-inspector-id"
        # ao longo de 5 segundos (ts 1000–5000), simulando uma rota.
        self.pings: List[LocationPing] = [
            LocationPing(
                user_id="fake-inspector-id",
                lat=-23.5505 + i * 0.001,
                lng=-46.6333 + i * 0.001,
                ts=1000 + i * 1000,
                ts_device=950 + i * 1000,
                accuracy=5.0,
            )
            for i in range(5)
        ]

    def query_history(
        self, *, user_id: str, since_ms: int, until_ms: int
    ) -> List[LocationPing]:
        filtered = [
            p for p in self.pings
            if p.user_id == user_id and since_ms <= p.ts <= until_ms
        ]
        return sorted(filtered, key=lambda p: p.ts)
