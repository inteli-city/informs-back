"""Entidade LocationPing — um ponto de localização capturado por um inspector.

Persistido na tabela Location (provisionada pela FormulariosTrackingStack):
- PK = user#{user_id}
- SK = ts#{ts_server_ms}    (server timestamp pra evitar colisão)
- atributos: lat (N), lng (N), ts_device (N), accuracy (N opcional)

Domínio puro — não conhece DynamoDB nem JSON. Conversões ficam nos repos.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class LocationPing:
    user_id: str
    lat: float
    lng: float
    ts: int  # epoch ms gerado pelo servidor (canônico pra ordenação)
    ts_device: int  # epoch ms gerado pelo device (preserva cronologia real)
    accuracy: Optional[float] = None
