"""ConnectionRegistry — estado em memória das conexões ativas.

Estrutura:
- `motocas`: dict user_id → (websocket, last_known_location)
  - 1 motoca pode ter no máx 1 conexão ativa (segunda força disconnect da
    primeira pra evitar duplicação de pings).
- `gestores`: set de websockets (broadcast global, sem state por gestor).

Operações são síncronas e thread-unsafe — assumimos uvicorn rodando
single-process com 1 event loop. Se evoluir pra multi-worker, este módulo
precisa virar Redis pub/sub.
"""

from dataclasses import dataclass
from typing import Optional

from fastapi import WebSocket

from .messages import LocationOut


@dataclass
class MotocaConnection:
    websocket: WebSocket
    last_known: Optional[LocationOut] = None


class ConnectionRegistry:
    def __init__(self) -> None:
        self._motocas: dict[str, MotocaConnection] = {}
        self._gestores: set[WebSocket] = set()

    # ---------- MOTOCA ----------

    def register_motoca(
        self, user_id: str, websocket: WebSocket
    ) -> Optional[WebSocket]:
        """Registra motoca. Se já existia conexão pra esse user, devolve a antiga
        pro caller fechar (evita 2 sessões da mesma pessoa publicando pings)."""
        previous = self._motocas.get(user_id)
        self._motocas[user_id] = MotocaConnection(websocket=websocket)
        return previous.websocket if previous else None

    def unregister_motoca(self, user_id: str, websocket: WebSocket) -> bool:
        """Remove só se a conexão registrada for a mesma — evita race quando
        uma reconexão chega antes do cleanup da antiga."""
        current = self._motocas.get(user_id)
        if current and current.websocket is websocket:
            del self._motocas[user_id]
            return True
        return False

    def update_last_known(self, user_id: str, location: LocationOut) -> None:
        conn = self._motocas.get(user_id)
        if conn:
            conn.last_known = location

    def online_motocas(self) -> list[tuple[str, Optional[LocationOut]]]:
        return [(uid, c.last_known) for uid, c in self._motocas.items()]

    # ---------- GESTOR ----------

    def register_gestor(self, websocket: WebSocket) -> None:
        self._gestores.add(websocket)

    def unregister_gestor(self, websocket: WebSocket) -> None:
        self._gestores.discard(websocket)

    def gestores(self) -> list[WebSocket]:
        # cópia rasa pra permitir iteração segura quando o caller pode
        # modificar o set (ex: disconnect durante broadcast).
        return list(self._gestores)
