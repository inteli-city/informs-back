from abc import ABC, abstractmethod
from typing import List

from src.shared.domain.entities.location_ping import LocationPing


class ILocationRepository(ABC):
    """Operações sobre a tabela Location do tracking.

    Por enquanto só leitura — writes vivem no ws_server (FastAPI/uvicorn
    na Lightsail), não nas Lambdas REST.
    """

    @abstractmethod
    def query_history(
        self, *, user_id: str, since_ms: int, until_ms: int
    ) -> List[LocationPing]:
        """Retorna pings de um inspector no intervalo [since_ms, until_ms]
        (inclusivo dos dois lados), ordenados cronologicamente ascendente
        por ts (server timestamp). Pagina internamente se passar de 1MB."""
