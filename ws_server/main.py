"""FastAPI app — único endpoint WS `/ws` que serve INSPECTOR e ADMIN.

Decisão de não separar `/ws/inspector` e `/ws/admin`: o role já vem do
Profile (lookup pós-JWT), então a separação seria redundante e abriria
caminho pra cliente errar de path. Server decide o comportamento pelo
role descoberto.

Fluxo:
1. Conecta → handshake busca JWT no header → valida → lookup role.
2. Se role = INSPECTOR: registra na presence (emissor de localizações),
   broadcast presence:connect pros admins, escuta loop de pings.
3. Se role = ADMIN: registra na presence (consumidor), manda snapshot
   inicial, escuta (sem ler nada — admin é read-only por enquanto).
4. Disconnect → cleanup + broadcast presence:disconnect (se inspector).

Health endpoint `/health` pra liveness/readiness probes (e também
pro Caddy não bater 404 em GET / antes do TLS estar pronto).
"""

import asyncio
import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import ValidationError

from . import config
from .auth import AuthError, Authenticator, extract_token_from_headers
from .location_repo import LocationRepository
from .messages import LocationOut, LocationPing, OnlineEntry, PresenceEvent, Snapshot
from .presence import ConnectionRegistry


logger = logging.getLogger("informs-ws")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


# ----------------------- WS close codes ----------------------------
# Convenção da própria spec do WebSocket:
#  - 1000-2999: reservados pelo protocolo
#  - 3000-3999: registrados (IANA)
#  - 4000-4999: app-specific (uso livre)
WS_AUTH_FAILED = 4401
WS_INVALID_PAYLOAD = 4400
WS_INTERNAL = 4500


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inicializa singletons (settings, registry, repo, auth)."""
    settings = config.load()
    app.state.settings = settings
    app.state.registry = ConnectionRegistry()
    app.state.location_repo = LocationRepository(
        table_name=settings.location_table, region=settings.aws_region
    )
    app.state.authenticator = Authenticator(settings)
    logger.info("startup ok stage=%s region=%s", settings.stage, settings.aws_region)
    yield
    logger.info("shutdown")


app = FastAPI(lifespan=lifespan)


@app.get("/health")
async def health():
    return {"status": "ok", "stage": app.state.settings.stage}


@app.websocket("/ws")
async def ws_endpoint(websocket: WebSocket):
    """Único endpoint WS — papel é descoberto via JWT + Profile."""
    registry: ConnectionRegistry = websocket.app.state.registry
    repo: LocationRepository = websocket.app.state.location_repo
    auth: Authenticator = websocket.app.state.authenticator

    # Authenticate ANTES do accept — assim cliente recebe close handshake
    # com código semântico em vez de "connection rejected" genérico.
    token = extract_token_from_headers(dict(websocket.headers))
    try:
        user = await auth.authenticate(token)
    except AuthError as exc:
        logger.warning("auth fail: %s", exc)
        await websocket.close(code=WS_AUTH_FAILED, reason=str(exc)[:120])
        return

    await websocket.accept()
    logger.info("connect user=%s role=%s", user.user_id, user.role)

    if user.role == "INSPECTOR":
        await _serve_inspector(websocket, user.user_id, registry, repo)
    else:
        await _serve_admin(websocket, registry)


# ----------------------- handlers por role ----------------------------


async def _serve_inspector(
    websocket: WebSocket,
    user_id: str,
    registry: ConnectionRegistry,
    repo: LocationRepository,
) -> None:
    # Sessão duplicada: força disconnect da anterior.
    previous = registry.register_inspector(user_id, websocket)
    if previous is not None:
        try:
            await previous.close(code=4002, reason="reconectado em outra sessão")
        except Exception:
            pass

    # Notifica admins que inspector entrou online.
    await _broadcast_to_admins(
        registry, PresenceEvent(type="connect", user_id=user_id)
    )

    try:
        while True:
            raw = await websocket.receive_json()
            try:
                ping = LocationPing.model_validate(raw)
            except ValidationError as exc:
                # Mensagem inválida = erro do cliente, mas mantém conexão aberta.
                logger.info("payload inválido user=%s err=%s", user_id, exc)
                await websocket.send_json({"type": "error", "detail": "payload inválido"})
                continue

            ts_server = int(time.time() * 1000)
            try:
                repo.put_ping(
                    user_id=user_id,
                    lat=ping.lat,
                    lng=ping.lng,
                    ts_server=ts_server,
                    ts_device=ping.ts_device,
                    accuracy=ping.accuracy,
                )
            except Exception:
                # Falha de DDB não derruba a sessão; registramos e seguimos.
                # Próximo ping em 60s tenta de novo.
                logger.exception("erro ao gravar ping user=%s", user_id)

            location = LocationOut(
                user_id=user_id,
                lat=ping.lat,
                lng=ping.lng,
                ts=ts_server,
                ts_device=ping.ts_device,
                accuracy=ping.accuracy,
            )
            registry.update_last_known(user_id, location)
            await _broadcast_to_admins(registry, location)
    except WebSocketDisconnect:
        pass
    finally:
        if registry.unregister_inspector(user_id, websocket):
            await _broadcast_to_admins(
                registry, PresenceEvent(type="disconnect", user_id=user_id)
            )
        logger.info("disconnect inspector user=%s", user_id)


async def _serve_admin(websocket: WebSocket, registry: ConnectionRegistry) -> None:
    registry.register_admin(websocket)

    # Snapshot inicial: estado atual dos inspectors online.
    snapshot = Snapshot(
        online=[
            OnlineEntry(user_id=uid, last=last)
            for uid, last in registry.online_inspectors()
        ]
    )
    await websocket.send_json(snapshot.model_dump())

    try:
        # Admin é read-only — descartamos qualquer mensagem que mande.
        # Esse loop existe só pra detectar disconnect.
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        registry.unregister_admin(websocket)
        logger.info("disconnect admin")


# ----------------------- broadcast helper ----------------------------


async def _broadcast_to_admins(
    registry: ConnectionRegistry, message
) -> None:
    """Envia a mesma mensagem pra todos os admins online em paralelo.

    Falhas individuais não derrubam o broadcast — admin com socket morto
    é limpo silenciosamente; a próxima iteração do servidor já vai detectar.
    """
    payload = message.model_dump()
    admins = registry.admins()
    if not admins:
        return

    async def _send(ws: WebSocket):
        try:
            await ws.send_json(payload)
        except Exception:
            registry.unregister_admin(ws)

    await asyncio.gather(*(_send(ws) for ws in admins), return_exceptions=True)
