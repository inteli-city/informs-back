# Plano — Eventos e webhooks por sistema

**Status:** proposta para revisão · **Data:** 2026-10-10 · **Branch:** `feature/config-fase-5` (a partir de `feature/config-fase-4`, que traz o RBAC por sistema do #92)

É a "Fase 5 — Webhooks" do plano de evolução do produto. Não confundir com a "Fase 5 — Escala e mapa" da especificação de Uberlândia (§15): os nomes coincidem, os assuntos não.

## Objetivo

Avisar sistemas externos (uma API própria do cliente, um n8n, a Apex) quando algo acontece com um formulário. Cada **sistema** cadastra no Admin os seus webhooks: para onde mandar, quais eventos quer receber e um segredo para conferir que a chamada veio do Informs. O Admin mostra o histórico de cada entrega e deixa reenviar o que falhou.

Pedidos de origem: print de necessidades do produto, itens 2.1 (tomar OS em aberto), 2.2 (finalizar) e 2.3 (cancelar).

## Decisões já tomadas

| Tema | Decisão |
|---|---|
| Alcance de "trigger" | **Gatilho = evento do webhook.** Cada webhook escolhe em quais eventos dispara, sem condições extras. Filtros por template/prioridade e um motor de automação interno ficam fora (ver "Fora do escopo"). |
| Eventos | **Mapear todos os eventos da aplicação**, mesmo os que nenhuma regra de negócio usa hoje — para já existir a possibilidade. |
| Corpo da chamada | **Envelope fixo** (`event_type`, `event_data`, `event_meta`) e um `event_data` **estruturado por evento**, conforme a necessidade de cada um. |
| Acompanhamento | **Histórico de entregas + reenviar** no Admin. |

## Decisões em aberto (com recomendação)

| # | Decisão | Opções | Recomendação |
|---|---|---|---|
| D1 | Nome dos eventos | `form.sent` (ponto) ou `form-sent` (hífen) | **`form.sent`**: mesmo formato do catálogo de permissões (`forms.view_all`, `templates.manage`) e da maioria dos provedores de webhook. |
| D2 | Onde guardar o segredo de cada webhook | Secrets Manager (≈ US$ 0,40/segredo/mês, rotação pronta) · cifrado com KMS no próprio DynamoDB (≈ custo zero) | **KMS no DynamoDB**: um segredo por webhook em Secrets Manager cresce com o número de clientes; o KMS cifra o segredo e o item fica junto do cadastro. |
| D3 | Quem conduz o back | Tiago faz tudo e Gabriel revisa · dividir PRs | A definir com o Gabriel (ver "Execução"). |
| D4 | "Assumido do pool" também vale para atribuição pelo gestor? | um evento só · dois eventos | **Dois eventos** (`form.claimed` e `form.assigned`): quem recebe distingue pela origem; quem quer os dois assina os dois. |

## Fora do escopo

- **Condições no gatilho** (só template X, só prioridade alta): seria ABAC sobre o evento. Pode entrar depois como filtro no cadastro do webhook, sem mudar a entrega.
- **Motor de automação interno** (gatilho + condições + ações internas, como criar o próximo formulário ou atribuir alguém): é outra fase. Com webhooks, um **n8n externo** já cumpre esse papel — recebe o evento, aplica as condições e chama a API do Informs de volta.
- **Webhooks de entrada** (sistemas externos mandando eventos para o Informs): a Apex continua usando a API autenticada.
- **Tempo real no app** (WebSocket com eventos de formulário, especificação §10.1): reaproveita o mesmo stream e pode vir depois, como outro consumidor.

## Como é hoje

Levantamento no `informs-back` (branch `feature/config-fase-4`):

- **Histórico de eventos incompleto.** `FormEventType` (`src/shared/domain/enums/form_event_type_enum.py`) só tem `CLAIMED`, `RELEASED` e `ASSIGNED`. Criar, iniciar, enviar e cancelar não gravam evento. Os eventos que existem são gravados **depois** da atualização do formulário, num `put_item` separado (`claim_form`, `release_form`, `assign_form`): se o segundo falhar, o evento se perde. `RELEASED` não leva payload (a especificação, RN-UBE-010, pede o `assignment_source` anterior).
- **Chave do evento:** `PK = form#{form_id}`, `SK = event#{created_at:013d}#{id}` (`src/shared/infra/dtos/form_event_dynamo_dto.py`), na mesma partição do formulário.
- **Stream ligado e sem consumidor.** A tabela de formulários tem stream `NEW_IMAGE` (`iac/iac/dynamo_stack.py:32`) e nada o lê. Com `NEW_IMAGE` não dá para comparar antes/depois de um formulário — mas dá para ler **os itens de evento novos**, que é o que este plano usa.
- **Sem fila nem segredo.** Nenhum SQS, SNS, EventBridge bus, Secrets Manager ou KMS no CDK. `Environments` já declara `sqs_endpoint_url` (`src/shared/environments.py:97,125`) sem uso.
- **Saída para fora hoje:** só a sincronização com a Apex (`OriginRepositoryApex`, `urllib`, sem assinatura, sem tentativas na chamada, sem fila de mortos — ADR-0010). Depois do incidente de 2026-09-08 (dev/homolog mandando formulário de teste para a Apex de produção), a saída só liga em PROD (`apex_sync_enabled`). O mesmo risco vale para webhooks.
- **`SENT` não é usado.** Existe em `FormStatus`, mas nenhum caso de uso o grava (ADR-0008 previa). O envio do formulário termina em `COMPLETED`.
- **RBAC:** `Action` (`src/shared/domain/enums/action_enum.py`) e `AccessControl` comportam uma ação nova. Cuidado: `is_system_admin` compara as ações do papel com o catálogo inteiro (`access_control.py:43-44`) — ao criar uma 10ª ação, um papel personalizado que tem as 9 de hoje deixa de contar como admin do sistema, e isso afeta a liberação da Apex no `create_form`.

## Desenho

### 1. Catálogo de eventos

Todos gravados como `FormEvent`, **na mesma transação** que muda o formulário.

| Evento | Quando acontece | Caso de uso | `FormEventType` |
|---|---|---|---|
| `form.created` | formulário criado (no app, pela Apex, "para mim" ou "em aberto") | `create_form` | `CREATED` (novo) |
| `form.claimed` | assumido do pool por quem está em campo | `claim_form` | `CLAIMED` |
| `form.assigned` | atribuído a alguém por um gestor | `assign_form` | `ASSIGNED` |
| `form.released` | devolvido ao pool | `release_form` | `RELEASED` (passa a ter payload) |
| `form.started` | preenchimento iniciado | `start_form` | `STARTED` (novo) |
| `form.sent` | preenchido e enviado | `submit_form` | `SENT` (novo; o status do formulário segue `COMPLETED`) |
| `form.cancelled` | cancelado, com o motivo | `cancel_form` | `CANCELLED` (novo) |
| `webhook.test` | botão "Enviar teste" do Admin | rota de teste | — (não grava `FormEvent`) |

Evento novo entra pelo mesmo caminho: valor em `FormEventType`, escrita no caso de uso e uma linha no catálogo (`GET /webhooks/events`), que o Admin lê para montar a tela.

### 2. Corpo da chamada

Envelope igual para todos os eventos:

```json
{
  "event_id": "8f0c…",
  "event_type": "form.sent",
  "occurred_at": "2026-10-10T14:03:22.418Z",
  "event_data": { "…": "depende do evento" },
  "event_meta": {
    "system": "UBERLANDIA",
    "actor_user_id": "10ca…",
    "form_id": "b1f9…",
    "webhook_id": "wh_…",
    "delivery_id": "dl_…",
    "attempt": 1,
    "schema_version": 1,
    "environment": "prod"
  }
}
```

- `event_id` é o id do `FormEvent`: o mesmo evento reenviado mantém o id, e quem recebe usa isso para ignorar duplicatas.
- `schema_version` permite mudar o `event_data` de um evento sem quebrar quem já recebe.

`event_data` por evento (o resumo do formulário é comum a todos):

| Evento | `event_data` |
|---|---|
| todos | `form`: `id`, `title`, `template_id`, `status`, `possession`, `priority`, `external_id`, `service_type`, endereço (`street`, `number`, `area`, `city`), `latitude`, `longitude`, `user_id`, `assignment_source`, datas (`created_at`, `in_progress_at`, `completed_at`, `cancelled_at`) |
| `form.created` | `origin` (app, Apex, IA), `created_by` |
| `form.claimed` | `claimed_by` |
| `form.assigned` | `assigned_to`, `assigned_by` |
| `form.released` | `released_by`, `previous_user_id`, `previous_assignment_source` |
| `form.started` | `started_by` |
| `form.sent` | `sent_by`, `answers`: lista de `{ section_id, key, label, field_type, value }`, com as URLs dos anexos no `value` dos campos de arquivo |
| `form.cancelled` | `cancelled_by`, `reason`: `{ option, text, image_url }` |
| `webhook.test` | `message`: texto fixo, para conferir URL e assinatura |

Datas no envelope em ISO 8601 (UTC); no `event_data`, os mesmos timestamps em ms que a API já usa.

### 3. Cabeçalhos e assinatura

| Cabeçalho | Conteúdo |
|---|---|
| `Content-Type` | `application/json` |
| `User-Agent` | `Informs-Webhooks/1` |
| `X-Informs-Event` | `form.sent` |
| `X-Informs-Event-Id` | o `event_id` |
| `X-Informs-Delivery-Id` | id desta entrega (muda a cada reenvio manual) |
| `X-Informs-Timestamp` | segundos Unix do envio |
| `X-Informs-Signature` | `sha256=` + HMAC-SHA256 em hex de `"{timestamp}.{corpo}"` com o segredo do webhook |

Quem recebe recalcula o HMAC com o segredo e recusa diferenças ou timestamp com mais de 5 minutos (protege contra reenvio de uma chamada capturada). O plano entrega um exemplo de verificação em Python e em JavaScript (n8n).

### 4. Entrega

```
caso de uso grava formulário + FormEvent (transação)
  └─► stream do DynamoDB (INSERT de item `event#`)
        └─► Lambda `dispatch_form_events`
              lê os webhooks ativos do sistema inscritos no evento
              └─► SQS `informs-webhook-deliveries` (1 mensagem por webhook)
                    └─► Lambda `deliver_webhook`
                          POST assinado (timeout 10 s)
                          ├─ 2xx ............ entregue
                          ├─ 408/429/5xx/rede  tenta de novo com espera crescente
                          ├─ outro 4xx ...... falha definitiva, sem nova tentativa
                          └─ esgotou as tentativas → SQS DLQ + entrega marcada como falha
                          (cada tentativa grava uma linha no histórico)
```

- **Ler do stream, e não chamar de dentro de cada caso de uso:** pega toda mudança (app, sincronização com a Apex, correção manual) e não acopla os casos de uso aos webhooks — mesmo argumento da especificação §10.2 para o tempo real.
- **Filtro do stream:** só `INSERT` com `SK` começando com `event#` (filtro na event source mapping, sem custo de invocação para o resto).
- **Garantia:** pelo menos uma vez (*at-least-once*); quem recebe deduplica por `event_id`. **Sem garantia de ordem** entre eventos do mesmo formulário: o `occurred_at` diz a ordem.
- **Tentativas:** até 6, com espera de ~1 min, 5 min, 30 min, 2 h e 6 h (visibilidade da mensagem no SQS). Falhas parciais do lote com `BatchProcessor` do Powertools (já está nas dependências).
- **Fila de mortos:** após a última tentativa a mensagem vai para a DLQ e a entrega fica como **falha** no histórico; o Admin reenvia de lá.
- **Webhook inativo** ou apagado entre o evento e a entrega: a mensagem é descartada e o histórico registra o motivo.

### 5. Dados (tabela de formulários, single table)

| Item | PK | SK | Campos |
|---|---|---|---|
| Webhook | `system#{system}` | `WEBHOOK#{webhook_id}` | `name`, `url`, `events[]`, `active`, `secret_encrypted`, `secret_last4`, `created_by`, `created_at`, `updated_at` |
| Entrega | `webhook#{webhook_id}` | `delivery#{created_at:013d}#{delivery_id}` | `event_id`, `event_type`, `form_id`, `attempt`, `status` (`pending`/`delivered`/`failed`), `http_status`, `duration_ms`, `error`, `response_excerpt` (até 1 KB), `TTL` (30 dias) |

- O webhook fica na mesma partição da `SystemConfig` (`system#{system}` / `CONFIG`): listar os webhooks de um sistema é uma `Query` sem índice novo.
- O histórico usa o TTL que a tabela já tem configurado e ninguém usa.
- **Segredo:** gerado pelo servidor (32 bytes aleatórios), mostrado **uma vez** na criação ou na troca, guardado cifrado com uma chave KMS do projeto (D2). As leituras do Admin só devolvem `secret_last4`.

### 6. Rotas novas

| Rota | Faz | Permissão |
|---|---|---|
| `GET /webhooks/events` | catálogo de eventos com descrição e exemplo de corpo | autenticado |
| `GET /systems/{system}/webhooks` | lista os webhooks do sistema | `webhooks.manage` |
| `POST /systems/{system}/webhooks` | cria; devolve o segredo uma vez | `webhooks.manage` |
| `PUT /systems/{system}/webhooks/{id}` | edita nome, URL, eventos, ativo | `webhooks.manage` |
| `DELETE /systems/{system}/webhooks/{id}` | apaga | `webhooks.manage` |
| `POST /systems/{system}/webhooks/{id}/secret` | gera um segredo novo; devolve uma vez | `webhooks.manage` |
| `POST /systems/{system}/webhooks/{id}/test` | envia `webhook.test` agora e devolve o resultado | `webhooks.manage` |
| `GET /systems/{system}/webhooks/{id}/deliveries` | histórico (paginado, mais recente primeiro) | `webhooks.manage` |
| `POST /systems/{system}/webhooks/{id}/deliveries/{delivery_id}/redeliver` | reenvia aquela entrega (mesmo `event_id`, novo `delivery_id`) | `webhooks.manage` |

### 7. Permissão

- Ação nova **`webhooks.manage`** ("Cadastrar e acompanhar os webhooks do sistema") no `Action` e em `ACTION_DESCRIPTIONS`. Aparece sozinha na tela de Papéis do Admin, num contexto novo "Integrações" (`webhooks.*`).
- **Corrigir `is_system_admin` antes** de criar a ação: decidir pelo papel (`role_id == ADMIN` ou super admin), não por "tem todas as ações do catálogo".

### 8. Admin (front, `informs-front`)

Área nova **Integrações** em `/admin/integracoes`, para quem tem `webhooks.manage` em algum sistema, no desenho da Configuração e dos Papéis:

- **À esquerda:** os webhooks do sistema (com seletor de sistema quando houver mais de um) e "Novo webhook".
- **À direita, o webhook escolhido:**
  - nome, URL e ativo;
  - **eventos em switches**, agrupados (Formulários: criado, assumido, atribuído, devolvido, iniciado, enviado, cancelado), lidos de `GET /webhooks/events`;
  - **segredo:** mostrado uma vez ao criar ou trocar, com botão de copiar; depois só os 4 últimos caracteres;
  - **Enviar teste**, com o resultado (status HTTP, tempo, trecho da resposta);
  - **Histórico de entregas:** evento, formulário, tentativa, status HTTP, tempo, erro; filtro por "falhas"; **Reenviar** em cada linha.
- Exemplo de verificação da assinatura (Python e JavaScript) num painel de ajuda.
- Permissões com CASL, como o resto do Admin (`can('manage', 'Webhook', { system })`).

### 9. Segurança

- **Só `https`** fora do ambiente local.
- **Bloqueio de endereços internos (SSRF):** resolver o host antes de cada envio e recusar loopback, faixas privadas, link-local (incluindo `169.254.169.254`, metadados da AWS) e IPv6 equivalentes; **não seguir redirecionamentos**.
- **Ambientes:** em dev e homolog, entregas só para hosts de uma lista permitida (`WEBHOOKS_ALLOWED_HOSTS`) — a mesma lição do incidente da Apex. Em PROD, livre (com o bloqueio acima).
- Tempo limite de 10 s; corpo da resposta guardado só até 1 KB; segredo nunca em log nem em resposta depois de criado.
- O `event_data` leva só o que o próprio sistema já tem (o formulário dele); URLs de anexos seguem a regra de leitura do bucket (pendência da Fase 3: confirmar se precisam ser assinadas).

### 10. Observabilidade

- Métricas (Powertools): entregues, falhas, tentativas, mensagens na DLQ, latência.
- Logs estruturados com `event_id`, `delivery_id`, `webhook_id` e sistema (sem segredo nem corpo completo).
- Alerta quando a DLQ tiver mensagens, no mesmo esquema de push para o Kuma usado pelo `reconcile_form_files`.

### 11. Ambiente local

- LocalStack com `sqs` além de `s3` (`iac/local/docker-compose.yml`).
- **Leitor do stream local:** script que lê o stream do DynamoDB Local (a API de Streams funciona lá) e chama o `dispatch_form_events` no mesmo processo — como a API local faz com as rotas.
- **Worker local:** laço que lê a fila do LocalStack e chama o `deliver_webhook`.
- **Receptor de teste:** servidor simples em `127.0.0.1` que mostra cada chamada recebida e confere a assinatura; o seed cadastra um webhook apontando para ele.
- Em local, `http://127.0.0.1` liberado (só aqui).

### 12. Testes

- Casos de uso com repositórios mock, como o resto do projeto: escrita do evento em cada transição, catálogo, CRUD, troca de segredo, regras de permissão.
- Entrega: assinatura (vetor conhecido), classificação de resposta (2xx / 4xx / 408-429 / 5xx / timeout), bloqueio SSRF, montagem do `event_data` de cada evento.
- Repositórios Dynamo com fakes (o padrão do projeto), cobrindo a **transação** formulário + evento.
- Ponta a ponta no ambiente local: enviar um formulário pelo app e ver a chamada chegar assinada no receptor; derrubar o receptor e ver as tentativas e o reenvio pelo Admin.

## Execução

PRs pequenos, cada um revisável sozinho, abertos contra `feature/config-fase-5` (como as fases anteriores: a fase junta os PRs e vai para `dev` de uma vez). Tamanhos relativos (P, M, G).

### PR 1 — Todo evento registrado (back, M)
- [ ] `FormEventType`: `CREATED`, `STARTED`, `SENT`, `CANCELLED`.
- [ ] `create_form`, `start_form`, `submit_form` e `cancel_form` gravam o evento; `release_form` passa a gravar `previous_user_id`/`previous_assignment_source`.
- [ ] Formulário + evento numa **transação** (`TransactWriteItems` no repositório), inclusive nos três que já gravam evento hoje.
- [ ] Testes por caso de uso e do repositório.

### PR 2 — Cadastro de webhooks (back, M)
- [ ] Corrigir `is_system_admin` (decidir pelo papel ADMIN).
- [ ] `Action.WEBHOOKS_MANAGE` + descrição.
- [ ] Entidade `Webhook`, DTO, repositório (mock + Dynamo), segredo com KMS.
- [ ] Rotas de cadastro, troca de segredo e catálogo de eventos; CDK das Lambdas e da chave KMS.
- [ ] ADR-0021 (eventos e webhooks por sistema) como **Proposto**.

### PR 3 — Entrega (back, G)
- [ ] `dispatch_form_events` (consumidor do stream com filtro) e `deliver_webhook` (worker da fila).
- [ ] SQS + DLQ + permissões no CDK; event source mappings.
- [ ] Assinatura, classificação de resposta, tentativas, bloqueio SSRF, lista permitida fora de PROD.
- [ ] Histórico de entregas com TTL; rotas de histórico, teste e reenviar.
- [ ] Métricas e alerta da DLQ.

### PR 4 — Admin › Integrações (front, M)
- [ ] Queries das rotas novas; regra `Webhook` na ability do CASL.
- [ ] Tela no desenho de Configuração/Papéis: lista, editor com eventos em switches, segredo, teste, histórico e reenviar.
- [ ] Contexto "Integrações" na tela de Papéis (sai do prefixo `webhooks.*` sozinho).

### PR 5 — Ambiente local (back + front, P)
- [ ] SQS no LocalStack, leitor do stream e worker locais, receptor de teste, webhook no seed.
- [ ] `LOCAL_SETUP.md` atualizado.

**Ordem:** 1 → 2 → 3, com o 4 em paralelo ao 3 (depende só das rotas do 2) e o 5 junto do 3.

## Deploy

- [ ] PRs 1–3 aplicados e migração do RBAC (#92) já feita.
- [ ] Chave KMS criada pelo CDK; `WEBHOOKS_ALLOWED_HOSTS` definido em dev e homolog.
- [ ] Conferir no CloudFormation a criação da event source mapping no stream existente (não muda o tipo do stream).
- [ ] Cadastrar o primeiro webhook de Uberlândia (n8n ou API do cliente) e validar com "Enviar teste".

## Riscos

| Risco | Mitigação |
|---|---|
| Evento perdido se o formulário for gravado e o evento não | transação formulário + evento (PR 1) |
| Duplicatas em quem recebe | `event_id` estável; documentado como responsabilidade de quem recebe |
| Endpoint do cliente lento ou fora | fila com tentativas e DLQ; o app nunca espera a entrega |
| Webhook de dev/homolog chamando sistema real | lista de hosts permitidos fora de PROD |
| URL apontando para dentro da AWS | bloqueio SSRF e sem redirecionamentos |
| Payload grande no `form.sent` (muitas respostas) | só respostas e URLs de anexos, nunca os arquivos; limite de tamanho com aviso no histórico |
| Nova ação no catálogo mudando quem é admin de sistema | corrigir `is_system_admin` antes (PR 2) |

## Referências

- Especificação Uberlândia: §6.4 (histórico de posse), RN-UBE-008/010, §9.3 (saída para a Apex), §10 (tempo real a partir do stream).
- ADR-0008 (ciclo de vida do formulário), ADR-0010 (sincronização com a origem), ADR-0020 (RBAC por sistema com ações).
- Plano de evolução do produto (Claude Doc "Informs — Plano de evolução do produto"), Fase 5.
