"""Schemas do endpoint GET /mss-formularios/locations/history."""

from typing import List, Optional

from pydantic import Field

from src.shared.helpers.contracts.base import RequestContractModel, ResponseContractModel


class LocationHistoryRequestSchema(RequestContractModel):
    """Query params do endpoint.

    `since` e `until` são opcionais. Se ausentes, o controller assume
    "rota do dia" no fuso America/Sao_Paulo:
        since = início do dia atual em BRT (00:00 -03:00) → epoch ms UTC
        until = agora (epoch ms UTC)
    """

    user_id: str = Field(..., description="user_id (Cognito sub) do inspector")
    since: Optional[int] = Field(
        default=None, gt=0,
        description="início do range em epoch ms (inclusivo). Default: 00:00 BRT de hoje.",
    )
    until: Optional[int] = Field(
        default=None, gt=0,
        description="fim do range em epoch ms (inclusivo). Default: agora.",
    )


class LocationPingResponseSchema(ResponseContractModel):
    user_id: str
    lat: float
    lng: float
    ts: int
    ts_device: int
    accuracy: Optional[float] = None


class LocationHistoryResponseSchema(ResponseContractModel):
    items: List[LocationPingResponseSchema]
    count: int
