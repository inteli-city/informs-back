from abc import ABC, abstractmethod
from typing import Optional

from src.shared.domain.entities.geocoded_address import GeocodedAddress


class IReverseGeocoder(ABC):
    """Endereço de uma coordenada (geocodificação reversa)."""

    @abstractmethod
    def reverse(self, latitude: float, longitude: float) -> Optional[GeocodedAddress]:
        """Endereço do ponto, ou `None` se o serviço não achou endereço ali.

        Serviço fora do ar, sem configuração ou com resposta inesperada:
        `ReverseGeocodeUnavailable`."""
