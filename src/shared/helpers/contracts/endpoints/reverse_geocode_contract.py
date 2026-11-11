"""Schemas do endpoint GET /mss-formularios/geocode/reverse."""

from pydantic import Field

from src.shared.helpers.contracts.base import RequestContractModel, ResponseContractModel


class ReverseGeocodeRequestSchema(RequestContractModel):
    """Query params: o ponto cujo endereço se quer."""

    lat: float = Field(..., ge=-90, le=90, description="Latitude do ponto.")
    lng: float = Field(..., ge=-180, le=180, description="Longitude do ponto.")


class ReverseGeocodeResponseSchema(ResponseContractModel):
    street: str = Field(description="Rua. Vazia se o serviço não informou.")
    number: str = Field(description="Número como veio do serviço (pode ser '125-127'). Vazio se não informou.")
    city: str = Field(description="Cidade. Vazia se o serviço não informou.")
    formatted: str = Field(description="Endereço completo, para a pessoa conferir.")
