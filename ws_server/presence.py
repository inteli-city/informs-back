"""ConnectionRegistry — estado em memória das conexões ativas.

Estrutura:
- `inspectors`: dict user_id → (websocket, last_known_location)
  - 1 inspector pode ter no máx 1 conexão ativa (segunda força disconnect
    da primeira pra evitar duplicação de pings).
- `admins`: set de websockets (broadcast global, sem state por admin).

Operações são síncronas e thread-unsafe — assumimos uvicorn rodando
single-process com 1 event loop. Se evoluir pra multi-worker, este módulo
precisa virar Redis pub/sub.
"""

from dataclasses import dataclass
from typing import Optional

from fastapi import WebSocket

from .messages import LocationOut


@dataclass
class InspectorConnection:
    websocket: WebSocket
    last_known: Optional[LocationOut] = None


class ConnectionRegistry:
    def __init__(self) -> None:
        self._inspectors: dict[str, InspectorConnection] = {}
        self._admins: set[WebSocket] = set()

    # ---------- INSPECTOR ----------

    def register_inspector(
        self, user_id: str, websocket: WebSocket
    ) -> Optional[WebSocket]:
        """Registra inspector. Se já existia conexão pra esse user, devolve a
        antiga pro caller fechar (evita 2 sessões da mesma pessoa publicando
        pings)."""
        previous = self._inspectors.get(user_id)
        self._inspectors[user_id] = InspectorConnection(websocket=websocket)
        return previous.websocket if previous else None

    def unregister_inspector(self, user_id: str, websocket: WebSocket) -> bool:
        """Remove só se a conexão registrada for a mesma — evita race quando
        uma reconexão chega antes do cleanup da antiga."""
        current = self._inspectors.get(user_id)
        if current and current.websocket is websocket:
            del self._inspectors[user_id]
            return True
        return False

    def update_last_known(self, user_id: str, location: LocationOut) -> None:
        conn = self._inspectors.get(user_id)
        if conn is None:
            return
        # Protege snapshot do admin contra cenário onde app envia ping
        # live ANTES de despejar pings bufferizados antigos: sem essa
        # guarda, o snapshot ficaria mostrando posição obsoleta do buffer.
        if conn.last_known is None or location.ts_device >= conn.last_known.ts_device:
            conn.last_known = location

    def online_inspectors(self) -> list[tuple[str, Optional[LocationOut]]]:
        return [(uid, c.last_known) for uid, c in self._inspectors.items()]

    # ---------- ADMIN ----------

    def register_admin(self, websocket: WebSocket) -> None:
        self._admins.add(websocket)

    def unregister_admin(self, websocket: WebSocket) -> None:
        self._admins.discard(websocket)

    def admins(self) -> list[WebSocket]:
        # cópia rasa pra permitir iteração segura quando o caller pode
        # modificar o set (ex: disconnect durante broadcast).
        return list(self._admins)
