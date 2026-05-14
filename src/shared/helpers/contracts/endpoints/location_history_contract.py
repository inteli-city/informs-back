"""Schemas do endpoint GET /mss-formularios/tracking/history."""

from typing import List, Optional

from pydantic import Field

from src.shared.helpers.contracts.base import RequestContractModel, ResponseContractModel


class LocationHistoryRequestSchema(RequestContractModel):
    """Query params do endpoint."""

    user_id: str = Field(..., description="user_id (Cognito sub) do inspector")
    since: int = Field(..., gt=0, description="início do range em epoch ms (inclusivo)")
    until: int = Field(..., gt=0, description="fim do range em epoch ms (inclusivo)")


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
