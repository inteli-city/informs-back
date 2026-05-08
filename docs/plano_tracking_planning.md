# Plano — Tracking de Motoverificadores + Route Planner

**Branch**: `feat/tracking-and-route-planning`
**Status**: Plano aprovado — pronto para implementação
**Diagramas**: ver `vault-prod/Intelicity/Informs/`
- `arquitetura_c4.excalidraw` — C4 Container do Informs (atual + adições)
- `modelagem_dynamo_tracking.excalidraw` — modelagem das 3 tabelas novas

---

## Sumário

Adicionar duas capacidades novas ao Informs:

1. **Tracking de motoverificadores em tempo real** — app mobile envia GPS via WebSocket; gestor vê todos os motocas online no mapa, com última posição dos offline e rota percorrida no dia.
2. **Route Planner on-demand** — endpoint puro: dado uma lista de form_ids + ponto inicial + ponto final opcional, devolve a sequência ordenada (nearest-neighbor + Haversine).

Tudo dentro do Informs, seguindo a Clean Architecture já estabelecida.

---

## 1. Decisões consolidadas

| # | Item | Decisão |
|---|------|---------|
| 1 | Auth do app & web | Cognito (grupo `FORMULARIOS`) + RBAC em DynamoDB (Profile.role) |
| 2 | Frequência de captura | 60s — ~15 motocas, 8h/dia |
| 3 | Rota percorrida | Default desde 00:00 BRT do dia atual; gestor escolhe data |
| 4 | TTL de location | **Sem TTL** — guardar histórico indefinido |
| 5 | Detecção de offline | TTL 5min na tabela Connection + ping/heartbeat 60s |
| 6 | Snapshot inicial gestor | REST `GET /tracking/snapshot` antes de assinar WS |
| 7 | Idempotência batch | `PutItem` com `attribute_not_exists(SK)` — duplicado dropa |
| 8 | Multi-device motoca | Aceita; cada conexão é independente |
| 9 | Profile bootstrap | Gestor pré-cadastra (`POST /tracking/profiles`) |
| 10 | `active=false` | Bloqueia login; gestor não vê no mapa |
| 11 | Cache no Connection | Sim — guarda role/system/name no $connect |
| 12 | Route planner | `form_ids` explícito no body; `end` opcional (default termina no último); Haversine + nearest-neighbor |

---

## 2. Modelagem de dados (DynamoDB)

### 2.1 Tabela nova `informs-tracking-profile`

| Campo | Tipo |
|-------|------|
| PK | `user#{user_id}` |
| SK | `METADATA` |
| user_id | string (Cognito sub) |
| role | enum `MOTOCA` \| `GESTOR` |
| name | string |
| email | string |
| system | string (`GAIA`, `SGC`, `GEOVISTA`, `INTELIFLEETS`) |
| vehicle_plate | string \| null |
| active | bool |
| created_at | int (epoch ms) |
| updated_at | int (epoch ms) |

**GSI ByRole**:
- PK: `role#{role}`
- SK: `system#{system}#user#{user_id}`
- Uso: listar todos os MOTOCAs de um sistema; listar GESTORes ativos

### 2.2 Tabela nova `informs-tracking-connection`

| Campo | Tipo |
|-------|------|
| PK | `connection#{connection_id}` |
| SK | `METADATA` |
| connection_id | string |
| user_id | string |
| role | enum |
| system | string |
| name | string (cache do Profile) |
| connected_at | int (epoch ms) |
| last_seen_at | int (epoch ms) |
| ttl | int (epoch s) — **DynamoDB TTL ativo** |
| source_ip | string |

**GSI ByUser**:
- PK: `user#{user_id}`
- SK: `connection#{connection_id}`
- Uso: descobrir se um motoca tem conexão ativa

**GSI ByRole**:
- PK: `role#{role}`
- SK: `connection#{connection_id}`
- Uso: fan-out — listar todos os GESTORes conectados pra broadcast

**TTL**: `last_seen_at + 5min`. Renovado a cada `ping` ou `location` recebido. Após o TTL, item é apagado automaticamente pelo DynamoDB → conexão considerada zumbi.

### 2.3 Tabela nova `informs-tracking-location`

| Campo | Tipo |
|-------|------|
| PK | `user#{user_id}` |
| SK | `ts#{epoch_ms_zero_padded_13}` |
| user_id | string |
| latitude | number |
| longitude | number |
| accuracy | number \| null (metros) |
| speed | number \| null (m/s) |
| heading | number \| null (graus) |
| ts_device | int (epoch ms — timestamp do device, fonte da verdade) |
| server_received_at | int (epoch ms) |
| source | enum `REALTIME` \| `BUFFER_FLUSH` |
| connection_id | string \| null (apenas para REALTIME) |

**GSI ByDate**:
- PK: `user#{user_id}#date#{YYYY-MM-DD}` (data calculada de ts_device em BRT)
- SK: `ts#{epoch_ms}`
- Uso: query "rota do user X no dia Y" (eficiente)

**Idempotência**: PK `user#{user_id}` + SK `ts#{ts_device}` é a chave de dedup. Se o batch reenviar uma posição com o mesmo `ts_device`, `PutItem` com `ConditionExpression: attribute_not_exists(SK)` rejeita silenciosamente.

**Sem TTL** — histórico mantido indefinido.

---

## 3. Endpoints REST

Sob a API REST atual do Informs (`/mss-formularios`), adicionando o prefixo `/tracking`:

### 3.1 Profile (CRUD admin — apenas GESTOR)

| Método | Path | Descrição |
|--------|------|-----------|
| POST | `/tracking/profiles` | Cria profile (gestor pré-cadastra motoca) |
| GET | `/tracking/profiles` | Lista profiles com filtros `?role=&system=&active=` |
| GET | `/tracking/profiles/{user_id}` | Busca 1 profile |
| PUT | `/tracking/profiles/{user_id}` | Atualiza (nome, placa, sistema, active) |

### 3.2 Tracking — gestor

| Método | Path | Descrição |
|--------|------|-----------|
| GET | `/tracking/snapshot` | Lista todos os MOTOCAs com {última posição, online/offline, profile resumido}. Usado quando abre o mapa. |
| GET | `/tracking/users/{user_id}/route?date=YYYY-MM-DD` | Rota percorrida no dia (default = hoje BRT) |

### 3.3 Tracking — motoca

| Método | Path | Descrição |
|--------|------|-----------|
| POST | `/tracking/locations/batch` | Flush do buffer offline (lista de positions com ts_device de cada uma) |

### 3.4 Route Planner

| Método | Path | Descrição |
|--------|------|-----------|
| POST | `/tracking/route-plan` | Recebe `{start, end?, form_ids[]}` → retorna `{ordered_forms, total_distance_km}` |

---

## 4. WebSocket (API Gateway novo)

Stack CDK separado: `iac/iac/websocket_stack.py`. Stages: `dev`, `homolog`, `prod`.

### 4.1 Rotas

| Rota | Lambda | Descrição |
|------|--------|-----------|
| `$connect` | `tracking_ws_connect` | Lê JWT (via Lambda Authorizer), busca Profile, verifica `active=true`, cria Connection no DynamoDB |
| `$disconnect` | `tracking_ws_disconnect` | Remove Connection (best-effort — TTL faz cleanup garantido) |
| `$default` | (compartilhado) | Loga e ignora |
| `location` | `tracking_ws_location` | Motoca envia 1 posição em real-time → persiste + fan-out para GESTORes conectados |
| `ping` | `tracking_ws_ping` | Renova `last_seen_at` da Connection (TTL re-seta) |

### 4.2 Lambda Authorizer (`tracking_ws_authorizer`)

No `$connect`:
1. Lê `Authorization` (querystring `?token=...`, pois WebSocket não suporta header padrão pra autenticar `$connect` em alguns clientes)
2. Valida JWT contra Cognito user pool (mesma lib do Informs hoje)
3. Verifica grupo `FORMULARIOS`
4. Busca Profile do `sub` na tabela `informs-tracking-profile`
5. Rejeita se: profile não existe OU `active=false`
6. Retorna policy ALLOW + context `{user_id, role, system, name}` para o `tracking_ws_connect` consumir e cachear

### 4.3 Fan-out (broadcast realtime)

Quando `tracking_ws_location` recebe posição de um motoca:
1. Persiste em `informs-tracking-location` (idempotente)
2. Atualiza `last_seen_at` da Connection do motoca
3. Query GSI `ByRole` na tabela Connection com `role=GESTOR` → lista de connection_ids
4. Para cada gestor conectado, faz `apigatewaymanagementapi.post_to_connection(...)` com payload:
   ```json
   {
     "type": "location.update",
     "user_id": "...",
     "name": "...",
     "system": "GAIA",
     "latitude": -23.56,
     "longitude": -46.65,
     "ts_device": 1778195540000
   }
   ```
5. Se algum post retorna `GoneException` (410), remove a connection zumbi

---

## 5. Estrutura de módulos (Clean Architecture)

Cada lambda nova segue o padrão do Informs (presenter / controller / usecase / viewmodel):

```
src/modules/
├── tracking_create_profile/app/
├── tracking_get_profile/app/
├── tracking_get_all_profiles/app/
├── tracking_update_profile/app/
├── tracking_submit_locations_batch/app/
├── tracking_get_snapshot/app/
├── tracking_get_user_route/app/
├── tracking_plan_route/app/
├── tracking_ws_authorizer/app/
├── tracking_ws_connect/app/
├── tracking_ws_disconnect/app/
├── tracking_ws_location/app/
└── tracking_ws_ping/app/
```

### Shared adições

```
src/shared/
├── domain/
│   ├── entities/
│   │   ├── profile.py              # Profile entity
│   │   ├── connection.py           # Connection entity
│   │   └── location.py             # Location entity
│   ├── enums/
│   │   ├── profile_role_enum.py    # MOTOCA, GESTOR
│   │   └── location_source_enum.py # REALTIME, BUFFER_FLUSH
│   └── repositories/
│       ├── profile_repository_interface.py
│       ├── connection_repository_interface.py
│       └── location_repository_interface.py
├── infra/
│   ├── repositories/
│   │   ├── profile_repository_dynamo.py + _mock
│   │   ├── connection_repository_dynamo.py + _mock
│   │   └── location_repository_dynamo.py + _mock
│   └── dtos/
│       ├── profile_dto.py
│       ├── connection_dto.py
│       └── location_dto.py
└── helpers/
    ├── contracts/endpoints/
    │   ├── profile_contract.py
    │   ├── tracking_snapshot_contract.py
    │   ├── tracking_user_route_contract.py
    │   ├── tracking_locations_batch_contract.py
    │   └── route_plan_contract.py
    ├── external_interfaces/
    │   └── websocket_management_api.py  # wrapper boto3 apigatewaymanagementapi
    └── functions/
        ├── haversine.py
        └── nearest_neighbor.py
```

---

## 6. Algoritmo do Route Planner

### Inputs
```python
class RoutePlanRequestSchema:
    start: Coordinate         # {latitude, longitude}
    end: Coordinate | None    # opcional — se ausente, termina no último form
    form_ids: list[str]       # explícito, gestor escolhe na tela anterior
```

### Pipeline
1. Buscar lat/long de cada form em `form_ids` (Query individual ou BatchGetItem)
2. Validar que todos os forms existem (senão 404)
3. **Nearest-neighbor seedado em `start`**:
   ```
   current = start
   remaining = lista de forms
   ordered = []
   enquanto remaining:
       próximo = argmin(haversine(current, form) for form in remaining)
       ordered.append(próximo); remaining.remove(próximo); current = próximo
   ```
4. Se `end` fornecido: aplica swap simples no fim — se trocar último_form ↔ end reduz dist total, troca. (heurística leve)
5. Calcular `total_distance_km` (soma haversine no caminho ordenado)
6. Retornar lista ordenada com {form_id, latitude, longitude, form_title}

### Complexidade
- N=15: ~225 cálculos haversine = <1ms
- N=100: ~10k cálculos = ~10ms

Sem persistência. Stateless. Recomputável em qualquer momento.

---

## 7. Sequência de implementação (5 PRs incrementais)

A ideia é não juntar tudo num PR gigante — cada PR deve ser revisável/deployável isolado.

### PR 1 — Tabela Profile + CRUD REST
- IaC: tabela `informs-tracking-profile` + GSI ByRole
- Entidade `Profile` + DTO + repos (Dynamo + Mock)
- 4 lambdas (create, get, get_all, update)
- Schemas Pydantic
- Testes unitários
- ADR-0016: "Tracking — Profile separado do Cognito"

### PR 2 — Tabela Location + REST writes/reads
- IaC: tabela `informs-tracking-location` + GSI ByDate
- Entidade `Location` + DTO + repos
- `submit_locations_batch` (idempotente)
- `get_user_route?date=`
- Helper `haversine.py`
- Testes (idempotência, queries por data)
- ADR-0017: "Tracking — Modelagem de Location com idempotência por ts_device"

### PR 3 — WebSocket API + Connection mgmt + Authorizer
- IaC: stack `WebSocketStack` (API GW v2, stages, integração Lambda)
- Tabela `informs-tracking-connection` + 2 GSIs + TTL
- Entidade `Connection` + DTO + repos
- `tracking_ws_authorizer` (Lambda Authorizer)
- `tracking_ws_connect`, `tracking_ws_disconnect`, `tracking_ws_ping`
- Testes (Authorizer rejeita inactive; ping renova TTL)
- ADR-0018: "Tracking — WebSocket com Lambda Authorizer e TTL para connection cleanup"

### PR 4 — Realtime location + Fan-out + Snapshot
- Lambda `tracking_ws_location` — persiste + fan-out
- Helper `websocket_management_api.py`
- Lambda `tracking_get_snapshot` (REST)
- Testes de fan-out (mock do apigatewaymanagementapi)
- Tratamento de `GoneException` (410) → cleanup
- ADR-0019: "Tracking — Fan-out push direto via apigatewaymanagementapi"

### PR 5 — Route Planner
- Helper `nearest_neighbor.py`
- Lambda `tracking_plan_route` (REST)
- Schemas Pydantic
- Testes com casos conhecidos (verificar ordem ótima em N=3, N=5)
- ADR-0020: "Tracking — Route Planner com nearest-neighbor + Haversine"

---

## 8. Considerações de teste

- **Mocks**: Profile/Connection/Location têm versões `_mock` em `infra/repositories/` (mesmo padrão do `FormRepositoryMock`)
- **WebSocket Management API**: criar wrapper `WebSocketManagementApi` em `helpers/external_interfaces/`, com mock injetável nos testes de fan-out
- **Idempotência**: teste explícito que reenviar batch com mesmo `ts_device` não duplica
- **Algoritmo**: testes com N=3 e N=5 com posições conhecidas, comparando contra ordem ótima manual
- **Authorizer**: testes que cobrem todos os caminhos (token inválido, profile não existe, profile inativo, sucesso)

---

## 9. Considerações de segurança

| Endpoint | Quem pode |
|----------|-----------|
| `POST /tracking/profiles` | GESTOR |
| `GET /tracking/profiles` | GESTOR |
| `PUT /tracking/profiles/{id}` | GESTOR |
| `GET /tracking/snapshot` | GESTOR |
| `GET /tracking/users/{id}/route` | GESTOR |
| `POST /tracking/locations/batch` | MOTOCA dono (próprio user_id no token) |
| `POST /tracking/route-plan` | GESTOR |
| WebSocket `$connect` | qualquer profile ativo |
| WebSocket route `location` | apenas se a connection foi cacheada com role=MOTOCA |
| WebSocket fan-out destino | apenas connections com role=GESTOR |

A validação acontece em 2 camadas:
1. **Lambda Authorizer (WS)** — checa role no `$connect`
2. **Controller (REST/WS)** — re-checa role do requester user em cada operação sensível

---

## 10. Considerações de custo

Volume estimado:
- **15 motocas × 60 records/h × 8h × 22 dias úteis/mês = 158 400 location writes/mês**
- WebSocket messages = ~2× isso (envio do motoca + fan-out p/ N gestores). Para 5 gestores conectados: ~950 mensagens/mês.

Custo aproximado (sa-east-1, on-demand):
- DynamoDB writes: 158k × $1.25/1M = **~$0.20/mês**
- DynamoDB reads (snapshot + rotas): negligenciável
- WebSocket messages: 950k × $1.20/1M = **~$1.20/mês**
- Lambda invocations: ~160k/mês × $0.20/1M = **~$0.03/mês**

Total estimado: **<$5/mês** em homolog/prod (sem contar storage acumulado, que cresce ~5MB/mês).

---

## 11. Observabilidade

- Cada Lambda nova com **PowerTools logger** + structured logs (JSON) — mesmo padrão do `sync_forms_origin`
- Métricas custom (CloudWatch EMF):
  - `LocationsReceived` (count, por sistema)
  - `FanOutMessagesSent` (count, por gestor)
  - `FanOutGoneConnections` (count — connections zumbis removidas)
  - `RoutePlannerCalls` (count, com forms_count e duration_ms)
- Dashboards CloudWatch separados pra Tracking (não misturar com sync_forms)

---

## 12. Riscos e mitigações

| Risco | Mitigação |
|-------|-----------|
| `$disconnect` não chega → connection zumbi | TTL 5min na tabela Connection |
| Fan-out lento se muitos gestores | Aceitar como limitação inicial; futuro: SQS fila intermediária |
| Idempotência depende de ts_device confiável | Documentar no contrato com app mobile; rejeitar ts_device > now+5min como sanity check |
| Volume de location explode (motoca esquece app aberto) | Adicionar rate-limit no batch endpoint (ex: máx 1000 positions/batch) |
| Crescimento da tabela Location (sem TTL) | Monitorar; se virar problema, mover para S3 + Athena pra arquivo |

---

## 13. Não está no escopo deste plano

- Notificações push (FCM) pra alertar gestor de eventos
- Geofencing / alertas se motoca sair de área
- Replay de rota com timeline scrubbing avançada
- Integração Google Maps Distance Matrix (rota real com trânsito)
- Multi-tenant — segregar gestores entre empresas
- Audit log de quem viu o quê

Esses ficam pra futuras evoluções.
