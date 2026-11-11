from src.shared.domain.entities.geocoded_address import GeocodedAddress
from src.shared.domain.repositories.reverse_geocoder_interface import IReverseGeocoder
from src.shared.helpers.errors.usecase_errors import NoItemsFound


class ReverseGeocodeUsecase:
    """Endereço do ponto escolhido no mapa do Criar (o pin).

    O app não chama o serviço de endereço direto: a chave dele fica só aqui.
    Sem endereço para o ponto, `NoItemsFound` — o app avisa e a pessoa
    preenche à mão."""

    def __init__(self, geocoder: IReverseGeocoder):
        self.geocoder = geocoder

    def __call__(self, latitude: float, longitude: float) -> GeocodedAddress:
        address = self.geocoder.reverse(latitude, longitude)
        if address is None:
            raise NoItemsFound("Endereço não encontrado para este ponto")
        return address
