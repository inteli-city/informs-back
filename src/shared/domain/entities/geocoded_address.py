from dataclasses import dataclass


@dataclass(frozen=True)
class GeocodedAddress:
    """Endereço de um ponto do mapa, como o app precisa para preencher o
    formulário. Campo que o serviço não informou vem como string vazia."""

    street: str
    number: str
    city: str
    # Endereço completo, para a pessoa conferir.
    formatted: str
