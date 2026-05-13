"""Schemas pydantic dos payloads WS — único ponto que define o protocolo."""

from typing import Literal, Optional
from pydantic import BaseModel, Field


# ----------------------- MOTOCA → server -----------------------


class LocationPing(BaseModel):
    """Único tipo de mensagem que o servidor aceita do MOTOCA.

    `ts_device` é o timestamp em ms gerado no celular no momento da leitura
    do GPS. Usado pra ordenação consistente quando há buffer offline e
    pra dedup futura por idempotência.
    """

    lat: float = Field(..., ge=-90.0, le=90.0)
    lng: float = Field(..., ge=-180.0, le=180.0)
    ts_device: int = Field(..., gt=0)
    accuracy: Optional[float] = Field(default=None, ge=0.0)


# ----------------------- server → GESTOR -----------------------


class OnlineEntry(BaseModel):
    user_id: str
    last: Optional["LocationOut"] = None  # última posição conhecida


class Snapshot(BaseModel):
    """Enviado UMA vez logo após GESTOR conectar."""

    type: Literal["snapshot"] = "snapshot"
    online: list[OnlineEntry]


class LocationOut(BaseModel):
    """Fan-out de uma localização nova pros gestores."""

    type: Literal["location"] = "location"
    user_id: str
    lat: float
    lng: float
    ts: int  # epoch ms do server (ts de quando foi recebido)
    ts_device: int
    accuracy: Optional[float] = None


class PresenceEvent(BaseModel):
    """Disparado quando MOTOCA conecta/desconecta."""

    type: Literal["connect", "disconnect"]
    user_id: str


# Permite forward reference de OnlineEntry → LocationOut
OnlineEntry.model_rebuild()
