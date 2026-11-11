from typing import Dict, Optional, Tuple

from src.shared.domain.entities.geocoded_address import GeocodedAddress
from src.shared.domain.repositories.reverse_geocoder_interface import IReverseGeocoder


class ReverseGeocoderMock(IReverseGeocoder):
    """Endereços fixos por coordenada, para os testes. Ponto desconhecido: sem
    endereço."""

    addresses: Dict[Tuple[float, float], GeocodedAddress]

    def __init__(self):
        self.addresses = {
            (-18.918, -48.2772): GeocodedAddress(
                street="Avenida João Naves de Ávila",
                number="2121",
                city="Uberlândia",
                formatted="Avenida João Naves de Ávila, 2121, Santa Mônica, Uberlândia, Minas Gerais, Brasil",
            ),
        }

    def reverse(self, latitude: float, longitude: float) -> Optional[GeocodedAddress]:
        return self.addresses.get((latitude, longitude))
