# Plano — Migração para Postgres e serviço em container

**Status:** estudo para discussão (não aprovado) · **Data:** 2026-10-10 · **Branch:** `feature/config-fase-5`

Plano separado do de webhooks ([webhooks-por-sistema.md](webhooks-por-sistema.md)), mas escrito levando-o em conta. O objetivo aqui é **enxergar como o Informs ficaria em outro padrão** — banco Postgres e API como um serviço comum, sem Lambda, API Gateway e DynamoDB — e quanto custa chegar lá. Nada aqui está decidido.

## Por que considerar

- **O volume não pede serverless.** A especificação de Uberlândia fala em algumas centenas de OS abertas/fechadas por dia, ~5.000 no mapa (pico ~10.000) e ~15 fiscais em campo. Um Postgres pequeno e um container atendem com folga; o "escala a zero" do Lambda economiza pouco nesse tamanho.
- **O modelo de dados é relacional.** Formulários, eventos, templates, papéis, vínculos pessoa↔sistema, configuração por sistema. No DynamoDB isso virou 3 tabelas, 4 GSIs, item de trava para `external_id` e chaves compostas montadas à mão. Várias consultas já brigam com o modelo:
  - `GET /forms` sem `user_id` faz **Scan da tabela inteira** e filtra/ordena a busca em Python (`form_repository_dynamo.py`, `get_all_forms`).
  - `SystemConfig.list_all` é Scan com filtro.
  - formulário + evento não são gravados juntos (o `transact_write_items` existe e ninguém usa) — o plano de webhooks precisa disso.
  - mapa "só os pinos", delta por `updated_at` e filtro por bairro (especificação §14) são consultas triviais em SQL e exigem índice novo a cada uma no DynamoDB.
- **É o padrão da casa.** Os outros back-ends Python da Intelicity (recape, comgas, gates_backend) são FastAPI + Postgres (SQL com `text()`) + gunicorn em Docker. O próprio repositório já tem um serviço assim: o `ws_server` (FastAPI, Railway — ADR-0018).
- **Ambiente local e testes mais simples.** Hoje o local precisa de DynamoDB Local, LocalStack, criação de tabelas/GSIs à mão e um servidor que imita o API Gateway (`local_api.py`, branch `feature/local-env`). Com Postgres + o próprio app, é `docker compose up`.
- **Menos peças para os webhooks e o tempo real.** Stream + Lambda + SQS + DLQ + KMS viram uma tabela de entregas e um worker no mesmo código (ver "Webhooks neste padrão").

## O que se perde ou piora (honestamente)

- **Operação passa a ser nossa:** backup e restore do Postgres, atualização de versão, migrações de schema, monitorar memória/CPU do container, conexões. No Lambda + DynamoDB isso é da AWS.
- **Custo fixo:** container e banco ligados 24 h, mesmo sem uso. Em dev e homolog isso pesa proporcionalmente mais.
- **Escala automática** some: um pico grande precisa de mais réplicas configuradas (não deve acontecer no volume previsto).
- **Esforço:** 35 módulos, 11 repositórios, CI/CD, ambiente local e migração de dados. É um projeto de semanas, não um PR.

## Inventário — o que existe e para onde vai

| Hoje (AWS) | Onde está | No novo padrão |
|---|---|---|
| API Gateway REST (`/mss-formularios/...`), 33 rotas registradas à mão | `iac/iac/lambda_stack.py` | **App FastAPI** com os mesmos caminhos, atrás de um domínio próprio |
| 35 Lambdas Python 3.10, uma por módulo, layer com `src/shared` | `src/modules/*/app/*_presenter.py` | presenters viram **routers FastAPI**; controllers e usecases ficam como estão |
| Authorizer Cognito (claims em `requestContext.authorizer.claims`) | `iac_stack.py`, `UserGatewayDTO.from_api_gateway` | **middleware** que valida o JWT pelo JWKS do Cognito (o `ws_server/auth.py` já faz) |
| Cognito / Gates (login no front) | front: `@intelicity/gates-auth` | **fica** — o front não muda nada |
| DynamoDB: Formulários (3 GSIs), Profiles (1 GSI), Locations | `iac/iac/dynamo_stack.py` | **Postgres** (tabelas abaixo) |
| S3 com URL pré-assinada de PUT, leitura por URL pública do bucket | `file_repository_s3.py`, `s3_url.py` | **fica no S3** na primeira etapa (ver decisão M2) |
| EventBridge Scheduler: `sync_forms_origin` (5 min) e `reconcile_form_files` (1 h) | `lambda_stack.py` L399-470 | **worker** com agendador e trava no Postgres (`pg_try_advisory_lock`) |
| Stream do DynamoDB (sem consumidor) | `dynamo_stack.py:32` | sai; eventos ficam numa tabela e o worker lê dela |
| CloudWatch Logs / Powertools (só em 2 jobs) | presenters dos jobs | logs estruturados em stdout + `IObservability` (padrão da casa) |
| CDK + `cdk deploy` no CD | `.github/workflows/CD.yml` | **imagem Docker** construída no CI e publicada no provedor escolhido |
| `ws_server` (Railway) lendo Profiles e gravando Locations no DynamoDB | `ws_server/` | mesmo serviço, apontando para o Postgres |

## Arquitetura proposta

```
apps (web / native)  ──HTTPS──►  api.informs.<domínio>
                                   │
                                   ├─ api (FastAPI + gunicorn/uvicorn, N réplicas)
                                   │    ├─ JWT Cognito (JWKS) → usuário
                                   │    ├─ routers  → controllers → usecases (sem mudança)
                                   │    └─ repositórios *_postgres (SQLAlchemy text())
                                   │
                                   ├─ worker (mesma imagem, outro comando)
                                   │    ├─ agendador: sync Apex (5 min), reconcile (1 h)
                                   │    └─ webhooks: entregas pendentes (SKIP LOCKED)
                                   │
                                   ├─ ws (ws_server atual)  ◄── LISTEN/NOTIFY: tempo real
                                   │
                                   ├─ Postgres gerenciado (+ PostGIS)
                                   └─ S3 (arquivos, inalterado)
```

- **Uma imagem, três processos** (`api`, `worker`, `ws`): mesmo código de domínio, deploy junto, sem layer.
- `ws` pode continuar separado (é stateful, uma instância só — ADR-0018) e passar a escutar o Postgres em vez de esperar um POST de uma Lambda (especificação §10.2).

### Camadas: o que muda no código

A arquitetura em camadas paga a conta aqui: **usecases e controllers não sabem que existem Lambda ou DynamoDB.**

| Camada | Muda? |
|---|---|
| `domain/` (entidades, enums, `AccessControl`, interfaces `I*Repository`) | não |
| `modules/*/app/*_usecase.py` | não (salvo onde hoje se compensa a falta de transação) |
| `modules/*/app/*_controller.py` | não na etapa 1; depois, validação vai para o modelo Pydantic da rota |
| `modules/*/app/*_presenter.py` | **sim**: `lambda_handler(event)` → rota FastAPI |
| `shared/infra/repositories/*_dynamo.py` | **ganham irmãos `*_postgres.py`**; escolha por `environments.py` |
| `shared/helpers/external_interfaces/http_lambda_requests.py` | sai no fim (na etapa 1 um adaptador ainda o usa) |
| `iac/` | sai no fim; entram `Dockerfile`, `docker-compose.yml` e migrações |

### Contrato com o front (o que não pode mudar)

Levantamento no `informs-front`: o acoplamento com a AWS é pequeno.

- **Auth:** o front faz login direto no Cognito (Gates) e manda `Authorization: Bearer <idToken>`. O back novo valida esse mesmo token — **nada muda no front**.
- **Corpo de erro:** manter `{ error, message, statusCode, timestamp, path }`; o front lê `statusCode` (`shared/offline/sync/submit-error-helpers.ts`) e reconhece "formulário já enviado" para tornar o reenvio da fila offline idempotente.
- **Caminhos:** manter `/mss-formularios/...` para só a URL base mudar.
- **Paginação:** `last_evaluated_key` / `exclusive_start_key` estão tipados mas **nenhuma tela manda cursor**. O token opaco (ADR-0014) continua, agora codificando um cursor por chave (`updated_at`, `id`).
- **Timestamps** em ms (número), ids gerados no servidor, `base_version`/`version` da configuração: mantidos.
- **Arquivos:** URL pré-assinada de PUT e o cabeçalho `x-amz-checksum-sha256` do native continuam valendo enquanto os arquivos ficarem no S3.
- **Tipos:** `shared/types/package.json` gera os tipos a partir da URL do API Gateway — trocar pela URL nova.

## Modelo de dados (Postgres)

Das 3 tabelas e 4 GSIs para tabelas normais. Campos de formato livre continuam como JSONB (ADR-0004).

| Tabela | Chave | Colunas principais | Índices (substituem os GSIs) |
|---|---|---|---|
| `forms` | `id uuid` | `system`, `template_id`, `status`, `possession`, `priority`, `user_id`, `assignment_source`, `external_id`, endereço, `latitude`/`longitude` (+ `geom` PostGIS), datas; `sections`, `information_fields`, `justification`, `attributes` em JSONB | `(user_id, priority, status, created_at)` ← GSI1; `(system, updated_at, id)` ← GSI2; **parcial** `(system, priority, created_at) WHERE possession = 'OPEN'` ← GSI3 (pool); `UNIQUE (system, external_id)` ← item `LOCK`; GiST em `geom`; trigram em título/endereço para a busca |
| `form_events` | `id uuid` | `form_id` FK, `type`, `actor_user_id`, `payload` JSONB, `created_at` | `(form_id, created_at)` |
| `templates` | `id uuid` | `system`, `name`, `active`, definição JSONB | `(system, active, name)` |
| `system_configs` | `system` | campos de hoje + `app_config` JSONB, `app_config_version` | — |
| `app_config_default` | linha única | `app_config` JSONB, `version` | — |
| `profiles` | `user_id` | `name`, `email`, `super_admin`, `deleted_at` | parcial `WHERE super_admin` |
| `system_roles` | `(system, role_id)` | `name`, `actions text[]`, `is_default`, `fixed` | — |
| `system_memberships` | `(user_id, system)` | `role_id` FK | `(system, role_id)` ← GSI `ByRole` |
| `location_pings` | `(user_id, ts)` | `lat`, `lng`, `ts_device`, `accuracy` | **particionada por mês**, com retenção |
| `sync_states` / `sync_error_forms` | `(job, system)` / `(job, system, form_id)` | checkpoint e falhas da sincronização com a Apex | — |
| `webhooks` / `webhook_deliveries` | ver plano de webhooks | | `webhook_deliveries (status, next_attempt_at)` |

- **Transação de verdade:** formulário + evento (e + entregas de webhook) na mesma transação — o PR 1 do plano de webhooks fica trivial.
- **Concorrência:** as escritas condicionais de hoje viram `UPDATE ... WHERE status = :esperado` / `WHERE user_id IS NULL` e checagem de linhas afetadas — mesma semântica do "tomar do pool" (quem chega primeiro leva).
- **Migrações de schema:** versionadas no repositório (decisão M6), rodando antes do deploy.

## Webhooks neste padrão

O plano de webhooks foi desenhado sobre a infraestrutura de hoje (stream → Lambda → SQS → Lambda, segredo com KMS). No Postgres, o desenho fica menor e com a mesma garantia:

| Peça | Hoje (plano de webhooks) | Com Postgres |
|---|---|---|
| Registrar o evento | `FormEvent` na transação (`TransactWriteItems`) | `INSERT form_events` na transação |
| Disparar | stream do DynamoDB → Lambda `dispatch_form_events` | **na mesma transação**, uma linha em `webhook_deliveries` por webhook inscrito (*outbox*) |
| Fila e tentativas | SQS com visibilidade crescente + DLQ | worker: `SELECT ... WHERE status = 'pending' AND next_attempt_at <= now() FOR UPDATE SKIP LOCKED`; falha agenda `next_attempt_at`; esgotou → `failed` |
| Acordar o worker | evento do SQS | `NOTIFY webhook_delivery` + varredura a cada poucos segundos |
| Histórico | item com TTL de 30 dias | a própria `webhook_deliveries`; limpeza diária pelo agendador |
| Segredo | KMS | cifrado na aplicação (AES-GCM) com chave em variável de ambiente |
| Reenviar | nova mensagem no SQS | nova linha `pending` |

**Não muda:** catálogo de eventos, envelope, `event_data` por evento, assinatura HMAC, rotas, permissão `webhooks.manage`, tela do Admin e proteção SSRF. Só o transporte.

**Recomendação de ordem:** os PRs 1 e 2 dos webhooks (eventos e cadastro) e o PR 4 (Admin) servem aos dois padrões. O **PR 3 (entrega)** é o que mais depende da infra — vale **decidir sobre esta migração antes de começá-lo**, para não construir stream + SQS + KMS e desmontar logo depois. Se a migração for para frente, o PR 3 nasce já no formato *outbox* (dá para rodar sobre DynamoDB com um índice de entregas pendentes até a troca do banco, ou esperar a etapa 2).

## Etapas

Migração **por baixo do contrato**: o app nunca percebe, e cada etapa pode ir para produção sozinha.

### Etapa 0 — Preparar o terreno (P)
- [ ] **Domínio próprio para a API** (ex.: `api.informs...`) apontando para o API Gateway atual. Builds novas do app native e o callback da Apex passam a usar esse domínio. Sem isso, apps instalados com a URL do API Gateway gravada na build quebram na troca.
- [ ] Decisões M1–M7 (abaixo).
- [ ] ADR "Postgres e serviço em container" como **Proposto**, marcando quais ADRs serão substituídos (0001, 0002, 0007, 0011; 0014 ajustado).

### Etapa 1 — App FastAPI sobre o DynamoDB atual (M)
Troca o "como roda" sem trocar o "onde guarda".
- [ ] App FastAPI com as 33 rotas nos mesmos caminhos. Primeiro com um **adaptador genérico** (requisição FastAPI → `HttpRequest` → controller), o mesmo truque do `local_api.py`; depois cada presenter vira router com o modelo Pydantic na rota (OpenAPI saindo do código).
- [ ] Middleware JWT (JWKS do Cognito, grupos `FORMULARIOS` + sistemas) produzindo o mesmo `UserGatewayDTO`.
- [ ] Handler de erros com o corpo de hoje.
- [ ] `Dockerfile` + `docker-compose` + healthcheck `/health`.
- [ ] Rodar em dev **ao lado** das Lambdas, mesmo banco; o e2e do front contra os dois.

### Etapa 2 — Postgres (G)
- [ ] Schema e migrações; repositórios `*_postgres.py` para as 11 interfaces; `environments.py` escolhe por variável.
- [ ] Testes dos repositórios contra um Postgres de verdade no CI (container de serviço no GitHub Actions); os testes de usecase com mock seguem iguais.
- [ ] Script de migração **DynamoDB → Postgres** reaproveitando os DTOs (`from_dynamo` → entidade → linha), idempotente, com contagem e amostragem por tabela.
- [ ] Ensaios em dev e homolog até o script rodar limpo.

### Etapa 3 — Jobs e serviços satélites (M)
- [ ] Worker com agendador: `sync_forms_origin` (5 min) e `reconcile_form_files` (1 h), com trava no Postgres para não rodar em dobro com mais de uma réplica; heartbeat no Kuma como hoje.
- [ ] `ws_server` lendo perfis e gravando localizações no Postgres.
- [ ] Callback da Apex (`/forms/sync-origin/callback`) pelo domínio novo.

### Etapa 4 — Virada (P, com janela)
- [ ] Janela curta com escrita bloqueada (as filas offline do app guardam o que for feito em campo e reenviam depois — 5xx/sem rede seguem na fila).
- [ ] Export final → import → conferência de contagens.
- [ ] Domínio aponta para o serviço novo. App e Apex não mudam nada.
- [ ] **Volta atrás:** possível só dentro da janela (apontar o domínio de volta). Depois de reabrir a escrita, o caminho é corrigir para frente — manter um sync reverso não compensa nesse volume.

### Etapa 5 — Limpeza (P)
- [ ] Apagar `iac/` (CDK, Lambdas, tabelas — guardando um backup exportado das tabelas do DynamoDB), `LambdaHttpRequest`, repositórios Dynamo e mocks que só existiam para eles.
- [ ] CI/CD: imagem Docker por branch (`dev` → `homolog` → `prod`), migrações antes do deploy.
- [ ] Ambiente local: `docker compose up` (Postgres + api + worker + ws + MinIO/LocalStack para S3); some o `local_api.py`.
- [ ] ADRs substituídos marcados; `CLAUDE.md` atualizado.

**Ordem e paralelismo:** 0 → 1 → 2 → 3 → 4 → 5. Etapa 1 pode ir a produção sozinha (já tira API Gateway/Lambda do caminho). O plano de webhooks corre em paralelo até o PR 3 (ver acima).

## Decisões em aberto (com recomendação)

| # | Decisão | Opções | Recomendação |
|---|---|---|---|
| M1 | Onde rodar os containers e o Postgres | AWS (ECS Fargate + RDS) · Railway (onde já está o `ws_server`) · VM da empresa com docker-compose (como recape/comgas) | Decidir com quem opera. Critérios: backup automático do banco, mesma região dos usuários (São Paulo), custo de 3 ambientes. Ficar perto do S3 (sa-east-1) ajuda nas URLs pré-assinadas, mas não é obrigatório. |
| M2 | Arquivos | manter S3 · S3 compatível (MinIO, R2) | **Manter S3** na migração: o front não muda e não há arquivo para mover. As respostas guardam a URL completa do bucket; se um dia trocar, migrar para guardar só a chave e montar a URL na leitura. |
| M3 | Autenticação | manter Cognito/Gates · outro provedor | **Manter**: é a plataforma da empresa e o front não muda. |
| M4 | PostGIS | desde o início · só quando precisar | **Desde o início** (extensão barata): pinos por área do mapa, geofence de 200 m e roteirização ficam em SQL. |
| M5 | Agendador | worker com agendador + trava no Postgres · cron do provedor | **Worker com trava**: roda igual em local, dev e prod; não depende do provedor. |
| M6 | Migrações de schema | Alembic · arquivos SQL numerados | **Alembic com SQL explícito** (`op.execute`), coerente com o padrão de SQL cru com `text()`. |
| M7 | Ordem com os webhooks | migrar antes do PR 3 · webhooks completos na AWS e migrar depois | **Decidir antes do PR 3** (ver "Webhooks neste padrão"). |

## Riscos

| Risco | Mitigação |
|---|---|
| Apps native instalados com a URL do API Gateway na build | domínio próprio na etapa 0, com antecedência de algumas versões; manter o API Gateway respondendo até a base migrar |
| Diferença de comportamento entre repositórios Dynamo e Postgres | mesmos testes de usecase; testes de repositório contra Postgres real; e2e do front nas duas versões durante a etapa 1–2 |
| Dados que não batem na migração | script idempotente com contagem e amostragem; ensaios em dev/homolog; janela com escrita bloqueada |
| Pool de conexões esgotado | pool por processo dimensionado, `pgbouncer` se o provedor não tiver equivalente |
| Banco vira ponto único de falha | Postgres gerenciado com backup e PITR; restore testado antes da virada |
| Custo fixo maior em dev/homolog | instâncias pequenas; desligar homolog fora do horário se o provedor permitir |
| Sincronização com a Apex rodando em dobro ou em dev mandando para produção | trava no Postgres; `APEX_SYNC_ENABLED` segue só em PROD (lição de 2026-09-08) |
| Esforço maior que o previsto | etapas independentes; a etapa 1 sozinha já entrega valor (local simples, sem cold start) |

## Fora do escopo

- Trocar o Cognito/Gates ou o login do front.
- Mover os arquivos do S3.
- Reescrever usecases ou mudar regras de negócio — a migração é de infraestrutura.
- Juntar `ws_server` e API num processo só (possível depois; hoje o `ws` é stateful e de instância única).

## Referências

- Especificação Uberlândia: RNF-009 (volume do mapa), §10 (tempo real a partir de eventos), §11 (geofence), §14 (escala do mapa e delta).
- ADR-0001, 0002, 0007, 0011, 0014 (substituídos ou ajustados por este plano); ADR-0018 (`ws_server` em FastAPI); ADR-0020 (RBAC por sistema).
- Plano de webhooks: [webhooks-por-sistema.md](webhooks-por-sistema.md).
- Padrão de back-end Python da Intelicity (FastAPI, Postgres com SQL cru, Docker).
