# informs-ws-server

Servidor WebSocket de tracking realtime de motoverificadores (Informs).
Roda numa Lightsail compartilhada provisionada pelo `iac/iac/tracking_stack.py`
(PR #45).

## Arquitetura

```
                          ┌─────────────────────────────┐
                          │   Lightsail Debian 12 $5    │
                          │                             │
  inspector app  ─wss──┐     │  Caddy :443                 │
                    └────►│   ├─ dev-IP.sslip.io  ─►:8001
  admin web  ─wss──┐     │   ├─ homolog-IP...    ─►:8002
                    └────►│   └─ prod-IP...       ─►:8003
                          │                             │
                          │  3× uvicorn (este código)   │
                          └──────┬──────────────────────┘
                                 │ boto3
                                 ▼
                          DynamoDB (informs-tracking-location-{env})
                          DynamoDB (informs-tracking-profile-{env})
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
python3.11 -m venv venv && source venv/bin/activate
pip install -e ".[dev]"

export STAGE=dev
export AWS_REGION=sa-east-1
export COGNITO_USER_POOL_ID=...
export COGNITO_APP_CLIENT_ID=...

uvicorn main:app --host 127.0.0.1 --port 8001
```

## Tests

```bash
pytest tests/ws_server -q   # da raiz do repo
```

43 testes (unit + integração via TestClient + DDB via moto).
