# informs-ws-server

Servidor WebSocket de tracking realtime de inspectors (Informs).
Roda no **Railway** (build via Dockerfile) — ver [`RAILWAY.md`](./RAILWAY.md)
pra setup completo.

## Arquitetura

```
                          ┌─────────────────────────┐
  inspector app  ─wss──┐  │  Railway service        │
                       └─►│  (Dockerfile + uvicorn) │
  admin web      ─wss──┐  │                         │
                       └─►│  3 environments:        │
                          │  - dev / homolog / prod │
                          └──────┬──────────────────┘
                                 │ boto3 (AWS access key via env)
                                 ▼
                          DynamoDB Location (FormulariosTrackingStack)
                          DynamoDB Profile  (FormulariosStack{stage})
```

## Protocolo

**INSPECTOR → server** (único tipo aceito):
```json
{"lat": -23.5, "lng": -46.6, "ts_device": 1715000000000, "accuracy": 5.5}
```

**server → ADMIN**:
- snapshot inicial (1×, logo após conectar):
  ```json
  {"type":"snapshot","online":[{"user_id":"u1","last":{...}}, ...]}
  ```
- presence:
  ```json
  {"type":"connect","user_id":"u1"}
  {"type":"disconnect","user_id":"u1"}
  ```
- location fan-out:
  ```json
  {"type":"location","user_id":"u1","lat":..,"lng":..,"ts":..,"ts_device":..}
  ```

## Auth

JWT Cognito no header `Authorization: Bearer <id_token>` (ou
`Sec-WebSocket-Protocol: Bearer.<token>` como fallback pra browser puro).

Roles autorizadas no tracking (mesmas do Profile aplicacional, ADR #16):
- `INSPECTOR` — emite localizações (1 sessão por user, segunda kicka a primeira).
- `ADMIN` — consome o stream em tempo real (broadcast global, read-only).

Outras roles são rejeitadas no handshake.

## Rodando local

```bash
cd ws_server
uv sync --extra dev

export STAGE=dev
export AWS_REGION=sa-east-1
export AWS_ACCESS_KEY_ID=... AWS_SECRET_ACCESS_KEY=...
export COGNITO_USER_POOL_ID=... COGNITO_APP_CLIENT_ID=...
export LOCATION_TABLE=... PROFILE_TABLE=...

uv run uvicorn main:app --host 127.0.0.1 --port 8001
```

## Tests

```bash
pytest tests/ws_server -q   # da raiz do repo
```

46 testes (unit + integração via TestClient + DDB via moto).

## Deploy

Push em `dev`/`homolog`/`prod` → Railway detecta a mudança em
`ws_server/**`, builda Docker, deploya no environment correspondente.
Setup completo em [`RAILWAY.md`](./RAILWAY.md).
