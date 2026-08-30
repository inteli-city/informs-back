# Especificação — Informs para Uberlândia (SGISV · Tapa-Buraco)

**Status**: Rascunho para validação
**Data**: 2026-08-30
**Público**: equipe de desenvolvimento Intelicity (backend + frontend)
**Fontes**: `SGISV_App_TapaBuraco_Documentacao_Tecnica.pdf` e `SGISV_App_TapaBuraco_Documentacao_projeto_de_telas.pdf` (especificação do gestor) + análise do código de `informs-back` e `informs-front`

---

## 1. Objetivo e recorte

Uberlândia contrata o Informs para operar o app de campo de tapa-buraco do SGISV, substituindo o app hoje gerado pelo Apex. A lacuna estrutural em relação ao que o Informs faz hoje é um **segundo modo de distribuição de trabalho**: a OS aberta, que qualquer equipe do escopo vê e a primeira que reivindicar leva.

**Os dois modos coexistem no mesmo contrato**, decididos OS a OS pelo sistema origem — não são configurações mutuamente exclusivas. Uberlândia usará predominantemente o modo aberto, mas continua podendo direcionar uma OS a uma pessoa específica quando quiser.

| | Direcionada (existe hoje) | Aberta (a construir) |
| --- | --- | --- |
| Criação da OS | Sistema origem informa o responsável | Sistema origem **omite** o responsável |
| Visibilidade | Só o destinatário vê | **Todas as equipes do escopo veem** |
| Posse | Definida na criação | **Quem reivindica primeiro fica com ela** |
| Efeito da posse | — | **Some da lista dos demais** |
| Passo de reivindicar | não existe — já é do destinatário | obrigatório antes de executar |

O que muda no domínio é, portanto, que **a posse deixa de ser obrigatória na criação** — não que ela deixe de existir.

Todo o resto da especificação do gestor (mapa, fichas, execução, cancelamento, geração de OS em campo, perfil, offline, tempo real, geofencing) é lido aqui contra o que o Informs já faz, para separar o que é reuso do que é construção.

Este documento **não** é um plano de implementação linha a linha: é o contrato de requisitos, o modelo de dados alvo e o inventário honesto de lacunas, com as decisões já tomadas registradas e as pendências nominadas.

### 1.1 Decisões já tomadas (Intelicity)

| # | Decisão | Registrada em |
| --- | --- | --- |
| D1 | O client será o **PWA** da branch `pwa-test` do `informs-front`, sobre o **mesmo backend** | §5 |
| D2 | Posse **individual**: reivindicada, a OS some para **todos** os demais usuários | §6, RN-UBE-003 |
| D3 | Libera o pool: **devolução manual pelo dono** e **reatribuição por Gestor/Fiscal**. Cancelamento **encerra**, não devolve | §6 |
| D4 | Escopo regional por **atributos genéricos chave/valor**, com interseção de conjuntos — sem código específico de cliente | §7 |
| D5 | Entrada das OS: **Apex chama `POST /forms`**, como o Gaia hoje | §9 |
| D6 | Tempo real: **reaproveitar o WebSocket** já existente (`ws_server`) | §10 |
| D7 | Geofencing: **sim**, genérico e **configurável por system**, validado no cliente e no backend | §11 |
| D8 | **Direcionamento continua disponível**: o sistema origem pode criar a OS já com responsável. Pool e direcionamento **coexistem no mesmo contrato**, decididos OS a OS | §6 |

---

## 2. Glossário e de-para SGISV ↔ Informs

| SGISV / Apex | Informs | Observação |
| --- | --- | --- |
| OS (Ordem de Serviço) | `Form` | Mesma entidade; a OS é um formulário georreferenciado |
| Ficha | item da listagem de `Form` | — |
| Pin | `Form` no mapa, colorido por `status` | — |
| Origem (Cidadão / IA / campo) | **não existe** | Campo novo (§8) |
| Permissão regional (bairros) | **não existe** | Escopo por atributos (§7) |
| Gestor / Fiscal / Executor | `ProfileRole` (hoje só `ADMIN`/`INSPECTOR`) | Papéis novos (§7.3) |
| Sistema origem (Apex) | `system` + `IOriginRepository` | Uberlândia = novo valor de `system` |
| Tabela "na equipe" (Apex) | evento de **abertura** da OS | `created_by` + `origin` |
| Tabela "concluído" (Apex) | evento de **conclusão** da OS | `completed_by` (campo novo) |
| Sync | fila de mutations offline + push para o Apex | Ambos já existem |

**Status do pin (RN-005) → `FormStatus`:**

| Cor | Spec | `FormStatus` | Posse |
| --- | --- | --- | --- |
| Vermelho | não iniciada | `PENDING` | `user_id = null` (pool) **ou** reivindicada e não iniciada |
| Amarelo | em andamento | `IN_PROGRESS` | sempre com dono |
| Verde | concluída | `COMPLETED` | dono = quem concluiu |
| — | encerrada por cancelamento | `CANCELLED` | — |

> O status `SENT` do enum atual não é usado por Uberlândia.

---

## 3. O que o Informs já entrega (inventário)

Levantamento feito sobre `informs-back@claude/informs-uberlandia-spec-74ijpu` e `informs-front` (branches `main` e `pwa-test`).

### 3.1 Backend — `informs-back`

**Arquitetura**: Clean Architecture por módulo (presenter → controller → usecase → repository), AWS Lambda + API Gateway + DynamoDB single-table + S3, IaC em CDK. Injeção de repositório por `STAGE` (`TEST` usa mocks in-memory). 107 arquivos de teste, ~12,4k linhas em `src/`.

| Capacidade | Onde | Reuso em Uberlândia |
| --- | --- | --- |
| Ciclo de vida da OS (`PENDING → IN_PROGRESS → COMPLETED/CANCELLED`) com timestamps por transição | `Form.start/complete/cancel/update_status` | **Direto** — cobre RN-008 |
| Concorrência otimista na escrita | `update_form(..., expected_status=)` | **Direto** — base do claim atômico |
| Motor de formulários por template | `Template`, `create/update/get_template` | **Direto** |
| **Seções duplicáveis** (`is_duplicable`, `section_instance`, máx. 50) | `Section.with_instance`, `Form._get_or_materialize_section` | **Direto** — é o "adicionar linha" das dimensões do buraco (RF-014) |
| 10 tipos de campo polimórficos, incluindo `FileField` com `min_quantity`/`max_quantity` | `src/shared/domain/entities/field.py` | **Direto** — limite de 10 fotos e antes/depois/extra (RF-015) |
| Justificativa de cancelamento com opções, texto e imagem (obrigatórios configuráveis) | `Justification`, `cancel_form` | **Direto** — cobre RF-019 e RF-020 inteiros |
| Upload por presigned URL + integridade (sha256/size/mimetype) + renovação + reconciliação S3 | `refresh_presign`, `reconcile_form_files`, `StoredFile` | **Direto** |
| Campos informativos, inclusive imagem de referência | `InformationField`, `FileInformationField` | **Direto** — foto da solicitação (RF-009) |
| Prioridade em 4 níveis | `Priority` (`LOW`/`MEDIUM`/`HIGH`/`EMERGENCY`) | **Direto** — casa 1:1 com baixa/média/alta/emergencial |
| Integração Apex/ORDS | `OriginRepositoryApex`, `sync_forms_origin` (EventBridge a cada 5 min, com checkpoint, fila de erro e callback) | **Parcial** — só saída (§9) |
| Paginação por token opaco + GSI2 (`system` + `updated_at`) | `get_forms_updated_since` | **Direto** — base do delta incremental |
| RBAC de perfil em tabela separada | `Profile`, `ProfileRole`, `create/delete/login_profile` | **Parcial** — faltam papéis, escopo e UPDATE (§7.3) |
| Tracking de localização + WebSocket próprio | `location_ping`, `get_location_history`, `ws_server/` (FastAPI no Railway) | **Parcial** — transporte pronto, protocolo só de GPS (§10) |
| Roteirização (vizinho mais próximo por prioridade) | `plan_route`, `haversine_km` | **Direto**; o haversine também serve ao geofencing |

### 3.2 Frontend — `informs-front`

Monorepo Yarn workspaces: `clients/native` (Expo/React Native, **em produção**), `clients/web` (PWA), `shared/*`.

**A branch `pwa-test` já é um PWA de campo funcional** — 205 arquivos alterados, ~27,5k linhas adicionadas sobre `main`:

| Capacidade | Onde (`pwa-test`) |
| --- | --- |
| PWA instalável, service worker, prompt de atualização | `vite-plugin-pwa` + Workbox em `clients/web/vite.config.ts`, `use-pwa-update.ts`, `pwa-update-banner.tsx` |
| Roteamento file-based tipado | TanStack Router (`clients/web/src/routes/`) |
| Autenticação Cognito PKCE por redirect + perfil de app | `@intelicity/gates-auth` (`createWebRedirectFlow`), `app-profile-store.ts`, `use-auth-gate.ts` |
| **Camada offline compartilhada entre native e web** | `shared/offline/` — adapters (`StorageAdapter`/`BlobStorageAdapter`/`NetworkAdapter`), Dexie no web, fila de mutations, scheduler de drenagem com backoff |
| Fila de mutations offline (`START`/`ANSWER`/`SUBMIT`/`CANCEL`) com atualização otimista e limite de 5 tentativas | `shared/offline/sync/mutation-queue-engine.ts`, `create-offline-sync-store.ts` |
| Criação de formulário offline | `create-offline-create-forms-store` (**bloqueada**: falta idempotência no `POST /forms` — ver `TODO.md`) |
| Mapa com clustering, ajuste de bounds, camada de rota | MapLibre + `forms-marker-cluster.tsx`, `fit-bounds-on-forms.tsx`, `route-plan-layer.tsx` |
| Preenchimento, anexos com armazenamento local, cancelamento, resumo | `fill-form.tsx`, `file-field-input.tsx`, `image-field-storage.ts`, `form-cancel-sheet.tsx` |
| Barra de sincronização e relatório de diagnóstico | `sync-status-bar.tsx`, `diagnostics-report.ts` |
| Testes e2e de fluxo online e offline | Playwright (`clients/web/e2e/offline-flow.spec.ts`, `online-flow.spec.ts`) |

**Conclusão do inventário**: a operação offline-first, o motor de formulários, o upload resiliente e o mapa já existem e são reaproveitáveis. O que falta é, quase inteiramente, **posse, escopo, tempo real e os campos de domínio da spec**.

---

## 4. Matriz de rastreabilidade da especificação

Legenda: **A** = atendido · **P** = parcial · **F** = falta.

### 4.1 Requisitos funcionais

| Req | Resumo | | Situação e lacuna |
| --- | --- | --- | --- |
| RF-001 a RF-003 | Login com usuário/senha, lembrar, esqueci a senha, mensagens de erro | P | Hoje o login é Cognito PKCE por redirect (Hosted UI). Tela própria de usuário/senha exige `USER_PASSWORD_AUTH`/SRP e assumir os fluxos de recuperação. **Pendência P4** |
| RF-004 | Sessão ≥ 20 min; sessões Informs/Apex segregadas | A | Tokens Cognito com refresh; sessões já são independentes |
| RF-005 | Home com abas Mapa e Fichas, padrão Mapa | P | Abas existem (`_tabs/`); rota padrão hoje é a lista. Ajuste de rota |
| RF-006 | Filtros: status, prioridade, programados, endereço/bairro e nº OS (autocomplete), limpar | P | UI de filtro existe; `get_all_forms` aceita status, system, intervalo de datas e busca textual em título/observação. **Faltam** prioridade, bairro, nº da OS e "início hoje" no backend, e a lista pré-carregada de logradouros. **Pendência P9** |
| RF-007 | Cor por prioridade + tarja de andamento | P | Hoje a cor é por status (`form-status-variants.ts`); prioridade já vem no dado. Ajuste visual |
| RF-008 | Ficha: endereço, nº OS, início e término esperados | P | Endereço existe. **Faltam** `external_id` (nº da OS do Apex) e `scheduled_start_at`; "término esperado" provavelmente mapeia em `expiration_date`. **Pendência P10** |
| RF-009 | Ficha detalhada: + tipo de serviço, data da ocorrência, origem, foto da solicitação | P | Foto e textos via `information_fields`. **Faltam** `origin` e `service_type` estruturados |
| RF-010 | "Ver no mapa" abrindo Google Maps web | A | `linking-maps.ts` no native; equivalente trivial no web |
| RF-011, RF-012 | Ações Executar/Cancelar; X e Voltar | A | `use-form-actions.ts`, `form-cancel-sheet.tsx` |
| RF-013 | Horas travadas, comentários, dimensões do buraco | P | Coberto por template. **Falta** marcar campo como somente-leitura no motor (hoje `Field` tem `required`, não tem `readonly`) |
| RF-014 | "Adicionar linha" para vários buracos | A | Seções duplicáveis |
| RF-015 | Antes/depois/extras, limite 10, feedback verde | A | `FileField` com `min_quantity`/`max_quantity` + UI |
| RF-016, RF-017 | Salvar sem concluir (amarelo) / concluir (verde) | A | `start` + `ANSWER` parcial; `submit` |
| RF-018 | Execução bloqueada fora do raio | **F** | Geofencing inexistente (§11) |
| RF-019, RF-020 | Cancelamento: motivo, justificativa, evidência | A | `Justification` cobre inclusive obrigatoriedade condicional |
| RF-021 | Centralizar na posição do usuário | P | **Falta** botão "Centralizar" e marcador da própria posição no web |
| RF-022 | Busca autocompletável + escala em metros | P | Escala é config do MapLibre; **falta** a base de logradouros/bairros. **Pendência P9** |
| RF-023, RF-024 | Pins por status; ação pelo pin | A | `forms-marker-cluster.tsx`, `map-form-card.tsx` |
| RF-025 | Camadas mapa e satélite | **F** | Hoje só o estilo vetorial OSM; precisa de uma fonte raster de satélite |
| RF-026 | Posição própria com heading | P | Geolocalização existe; heading no PWA depende de `DeviceOrientationEvent` (permissão explícita, precisão variável) |
| RF-027 | "Gerar OS em campo" só para perfis autorizados | P | A tela existe para todos; **falta** o gate por papel (§7.3) |
| RF-028 | Passo 1: pin arrastável estilo Uber, endereço reverso | **F** | Exige **reverse geocoding** — dependência externa nova. **Pendência P8** |
| RF-029, RF-030 | Passo 2: hora e endereço automáticos, fotos, controles fixos | P | Formulário existe; falta o desenho de 2 passos e os controles ancorados |
| RF-031 | Novo pin visível a todos em tempo real | **F** | Depende de §10 |
| RF-032 | Perfil: credenciais e regiões de atuação | P | Mostra nome/e-mail/papel; **falta** o escopo (§7) |
| RF-033 | Métricas de 30 dias | **F** | §12 |
| RF-034 | Sair | A | — |
| RF-035 | Câmera como padrão, galeria como alternativa | P | Ajuste do atributo `capture` no input de arquivo |
| RF-036 | Autoria de abertura e de fechamento em tabelas distintas | P | `created_by` e `user_id` existem; **faltam** `completed_by` e a segregação no payload de sync (§9) |

### 4.2 Requisitos não-funcionais

| Req | Resumo | | Situação e lacuna |
| --- | --- | --- | --- |
| RNF-001, RNF-002 | Offline com cache, fila e envio em pacote; compressão de fotos | A/P | Fila, persistência e drenagem com backoff prontos em `shared/offline/`. Verificar compressão de imagem no client web (no native é `expo-image-manipulator`) |
| RNF-003 | Política de conflito offline | **F** | **Crítico com o pool** — resolvido em §13 |
| RNF-004 | Propagação em poucos segundos | **F** | §10 |
| RNF-005 | Geofencing | **F** | §11 |
| RNF-006 a RNF-008 | Legibilidade sob sol, ações ao alcance do polegar, linguagem literal | P | Design system existe; exige passada de UI dedicada |
| RNF-009 | Mapa fluido com ~5.000 pins (pico ~10.000) | **P/F** | Clustering existe **no cliente**; no backend a consulta sem `user_id` cai em `Scan` da tabela inteira e o payload devolve o formulário completo. §14 |
| RNF-010 | HTTPS e permissões explícitas | A | — |
| RNF-011 | Sessão ≥ 20 min | A | — |
| RNF-012 | PWA instalável com service worker | A | `pwa-test`; resta o ícone maskable (já anotado no `TODO.md`) |
| RNF-013 | LGPD do rastreio contínuo (V02) | — | Fora do escopo da V01 |

### 4.3 Regras de negócio

| Regra | | Situação |
| --- | --- | --- |
| RN-001 permissão regional reflete de imediato | **F** | §7 + `PUT /profiles/{user_id}` |
| RN-002 prioridade reflete de imediato | **F** | Prioridade existe, mas **não há endpoint de atualização de OS pelo sistema origem** (§9.2) |
| RN-003 sessões segregadas | A | — |
| RN-004 geofencing | **F** | §11 |
| RN-005 cores por status | A | Mapeamento no §2 |
| RN-006 propagação em tempo real | **F** | §10 |
| RN-007 concluída fica visível em verde por ≥ 7 dias | **F** | Regra nova. **Pendência P6** |
| RN-008 transições de status | A | `Form.start/complete/cancel` |
| RN-009 origem da OS | **F** | Campo novo (§8) |
| RN-010 autoria segregada abertura/fechamento | P | Falta `completed_by` e o de-para no sync |
| RN-011 métricas em janela de 30 dias | **F** | §12 |

---

## 5. Plataforma (D1)

O client de Uberlândia é o **PWA em `clients/web`, branch `pwa-test`**, sobre o backend atual. Isso já atende RNF-012 e a premissa "Android-first, Chrome mobile, instalável" da spec.

Itens herdados da branch que continuam valendo como trabalho pendente (do próprio `TODO.md`):

1. `information_fields` **não são renderizados no web** — a foto da solicitação (RF-009) depende disso.
2. Criação de formulário offline **bloqueada** por falta de idempotência no `POST /forms` — impacta RF-028/029 em campo sem sinal.
3. Blobs órfãos no Dexie quando o progresso é descartado.
4. Paridade do offline: o native ainda mantém cópias próprias dos módulos que o web já consome de `shared/offline` (inclusive um bug de chave de cache que torna a atualização otimista um no-op silencioso no native).

> Os itens 1 e 2 são pré-requisitos funcionais de Uberlândia, não dívida cosmética.

---

## 6. Núcleo 1 — Pool aberto e reivindicação

É a feature que motiva o contrato. Hoje **todo** caminho de leitura e escrita do formulário é ancorado no dono: `Form.user_id` é obrigatório e validado como UUID; `get_form`, `start_form`, `submit_form` e `cancel_form` chamam `ensure_assigned_to`; `get_all_forms` sempre filtra pelo `user_id` do solicitante; o GSI1 é `user#{user_id}`. Não existe estado "sem dono" nem operação de reivindicar.

### 6.1 Modelo

- `Form.user_id` passa a ser **opcional**. `null` significa **aberta no pool**; preenchido significa **direcionada**, com o comportamento idêntico ao de hoje.
- Novos campos: `claimed_at`, `released_at`, `completed_by`, `assignment_source`.
- `assignment_source` ∈ `ORIGIN_SYSTEM` (direcionada na criação) · `CLAIM` (reivindicada no pool) · `MANAGER` (atribuída por Gestor/Fiscal). É o que permite ao Apex distinguir uma OS que ele direcionou de uma que a equipe pegou sozinha — e detectar quando um direcionamento seu foi rompido.
- `created_by` permanece como autoria de **abertura** (alimenta a tabela "na equipe" do Apex); `completed_by` passa a ser a autoria de **fechamento** (tabela "concluído") — RF-036 e RN-010.
- **Posse e execução são eventos distintos**: reivindicar (`claim`) tira a OS do pool sem mudar a cor do pin; o pin só fica amarelo ao salvar execução sem concluir (`start`), conforme RN-008.

### 6.2 Regras de negócio novas

| Regra | Enunciado |
| --- | --- |
| **RN-UBE-001** | OS com `user_id = null` e status `PENDING` está **aberta**: visível a todo usuário cujo escopo (§7) cubra os atributos da OS. OS com `user_id` preenchido está **direcionada**: nasce fora do pool, não aparece para mais ninguém e dispensa a reivindicação. **Os dois casos convivem no mesmo `system`** (decisão D8). |
| **RN-UBE-002** | A reivindicação é **exclusiva e atômica**. Implementada com `ConditionExpression` no DynamoDB (`attribute_not_exists(user_id)`), reaproveitando o padrão de `expected_status` já usado em `update_form`. O segundo a chegar recebe **409** com o nome do responsável atual. |
| **RN-UBE-003** | Reivindicada, a OS **sai da listagem de todos os demais usuários**, inclusive Gestor e Fiscal (decisão D2). ⚠️ **Diverge da spec**, cuja tabela de RBAC dá "cidade toda" a Gestor e Fiscal — ver **Pendência P3**. |
| **RN-UBE-004** | O dono pode **devolver ao pool** enquanto a OS não estiver concluída nem cancelada: `user_id` volta a `null`, `status` volta a `PENDING`, `in_progress_at` é limpo e `released_at` registrado. |
| **RN-UBE-005** | Gestor e Fiscal podem **reatribuir**: devolver ao pool uma OS de terceiro, ou atribuí-la diretamente a um usuário do escopo. |
| **RN-UBE-006** | O **cancelamento encerra** a OS (`CANCELLED`); não devolve ao pool. Mantém o comportamento atual do domínio. |
| **RN-UBE-007** | **Reivindicar, devolver e reatribuir exigem conectividade** — não entram na fila offline. Justificativa em §13. |
| **RN-UBE-008** | Toda transição de posse é registrada em histórico imutável (`claim`, `release`, `assign`), com autor, alvo e carimbo de tempo. |
| **RN-UBE-009** | **O responsável de uma OS direcionada sempre a enxerga**, mesmo que seu escopo regional não cubra os atributos dela. O escopo filtra o **pool**, não o trabalho que foi explicitamente atribuído a alguém — do contrário, o Apex direcionaria uma OS que a pessoa nunca veria. |
| **RN-UBE-010** | Devolver ao pool uma OS **direcionada** rompe a intenção do sistema origem, então o evento é registrado com `assignment_source` anterior e propagado ao Apex. Se a operação é permitida ao executor ou apenas ao Gestor/Fiscal — **Pendência P11**. |

> Expiração automática por tempo (a OS voltar sozinha ao pool) **não** entra nesta versão — fica registrada como evolução possível, já que exigiria um job de varredura e a definição de um prazo com o cliente.

### 6.3 Endpoints novos

| Método e rota | Quem pode | Efeito |
| --- | --- | --- |
| `POST /forms/{form_id}/claim` | qualquer usuário do escopo | `user_id = requester`, `claimed_at`. **409** se já tiver dono |
| `POST /forms/{form_id}/release` | dono; ou Gestor/Fiscal | `user_id = null`, `status = PENDING`, `released_at` |
| `POST /forms/{form_id}/assign` | Gestor/Fiscal | `user_id = alvo`, `claimed_at`. Corpo: `{ "user_id": "..." }` |

Alterações em endpoints existentes:

- `GET /forms` ganha o parâmetro `scope=pool|mine|all` (padrão `mine`, preservando o comportamento do Gaia).
- `GET /forms/{form_id}` deixa de exigir posse para **leitura** quando a OS está no pool e o escopo do solicitante a cobre (hoje devolve 403 para qualquer não-dono).
- `POST /forms` passa a aceitar `user_id` nulo (OS aberta) — é o que o Apex usará (D5).
- `start`, `submit` e `cancel` continuam exigindo posse: seguem chamando `ensure_assigned_to`, agora com mensagem específica quando a OS está no pool ("reivindique a OS antes de executá-la").

### 6.4 Histórico de posse

Nova entidade `FormEvent` no single-table (`PK = form#{form_id}`, `SK = event#{timestamp}#{uuid}`), com `event_type`, `actor_user_id`, `target_user_id` e `payload`. Barato (mesma partição do formulário), auditável, e serve de base para a linha do tempo da OS no Apex.

---

## 7. Núcleo 2 — Escopo e RBAC genéricos (D4)

**A preocupação levantada é legítima**: se cada contrato trouxer o próprio filtro customizado, o Informs deixa de ser um produto e vira N produtos. A saída é o Informs **não saber o que é "bairro"** — só saber comparar conjuntos.

### 7.1 Mecanismo

Duas estruturas, uma única regra:

```
Form.attributes : Dict[str, List[str]]     # ex.: {"bairro": ["Santa Mônica"], "visible_to": ["equipe-leste"]}
Profile.scope   : Dict[str, List[str]]     # ex.: {"bairro": ["Santa Mônica", "Tibery"]}
```

**Regra de visibilidade** — para cada chave `k` presente em `Profile.scope`:

```
interseção( Form.attributes.get(k, []) , Profile.scope[k] ) ≠ ∅
```

Consequências desse desenho:

- Chave **ausente** no escopo do perfil = **sem restrição** naquela dimensão.
- `scope = {}` = vê tudo do `system` → **é exatamente o comportamento atual, então Gaia, Geovista e SGC não mudam**.
- Gestor e Fiscal de Uberlândia = `scope` vazio na chave `bairro` → cidade toda, sem regra especial.
- A mesma engine cobre as duas ideias que discutimos: escopo geográfico (`bairro`) e lista de elegíveis vinda do sistema origem (`visible_to`) — porque ambos reduzem a interseção de conjuntos. O Apex pode mandar uma ou outra sem que o Informs precise saber a diferença.
- Nada aqui é específico de Uberlândia: é uma capacidade do produto, configurada por contrato.

### 7.2 Configuração por contrato

Nova configuração por `system` (entidade `SystemConfig` no single-table, `PK = system#{system}`, `SK = CONFIG`):

| Chave | Uberlândia | Gaia |
| --- | --- | --- |
| `scope_keys` | `["bairro"]` | `[]` |
| `scope_partition_key` | `"bairro"` | `null` |
| `geofence_radius_m` | a confirmar (§11) | `null` (desligado) |
| `allow_unassigned_forms` | `true` | `false` |

`allow_unassigned_forms` controla apenas se o contrato **aceita** OS sem responsável na criação. Com `false`, o Gaia mantém a validação atual de `user_id` obrigatório — **nenhuma regressão no contrato em produção**. Com `true`, Uberlândia pode enviar OS abertas **e** direcionadas, caso a caso: a flag habilita o modo aberto, não desliga o direcionado.

### 7.3 Papéis

`ProfileRole` ganha `MANAGER` (Gestor) e `SUPERVISOR` (Fiscal), preservando `ADMIN` e `INSPECTOR` (Executor).

| Capacidade | ADMIN | MANAGER | SUPERVISOR | INSPECTOR |
| --- | --- | --- | --- | --- |
| Ver OS do próprio escopo | ✓ | ✓ | ✓ | ✓ |
| Reivindicar, executar, cancelar | ✓ | ✓ | ✓ | ✓ |
| Gerar OS em campo (RF-027) | ✓ | ✓ | ✓ | ✗ |
| Reatribuir/devolver OS de terceiro | ✓ | ✓ | ✓ | ✗ |
| Gerenciar perfis | ✓ | ✗ | ✗ | ✗ |
| Ver posição das equipes (V02) | ✓ | ✓ | ✗ | ✗ |

Em V01, Gestor e Fiscal são idênticos — a distinção só aparece na V02, como a própria spec registra.

### 7.4 Sincronização do escopo (RN-001)

O `Profile` **não tem endpoint de atualização** hoje (`IProfileRepository` expõe apenas `get_by_user_id`, `create`, `soft_delete` e `count_active_by_role`). Para atender RN-001 e RN-002:

- **`PUT /profiles/{user_id}`** (novo): o Apex empurra `role` e `scope` quando a permissão regional muda. Reflexo imediato, na direção que já funciona hoje (Apex → Informs).
- O client revalida o próprio perfil no login e ao receber um evento de perfil pelo WebSocket (§10).

---

## 8. Núcleo 3 — Campos de domínio da especificação

Campos novos em `Form`, todos opcionais para não afetar os contratos existentes:

| Campo | Tipo | Atende | Observação |
| --- | --- | --- | --- |
| `external_id` | `str?` | RF-008, RF-009 | Número da OS/solicitação no Apex. **Deve ser a chave de idempotência** da ingestão (§9.1) |
| `origin` | enum `CITIZEN` / `AI` / `FIELD` / `ORIGIN_SYSTEM` | RF-009, RN-009 | Origem da demanda |
| `service_type` | `str?` | RF-009 | Tipo de serviço |
| `occurred_at` | `int?` | RF-009 | Data da ocorrência |
| `scheduled_start_at` | `int?` | RF-008 | "Início esperado" (**Pendência P10**) |
| `completed_by` | `str?` | RF-036, RN-010 | Autoria de fechamento |
| `attributes` | `Dict[str, List[str]]` | §7 | Escopo genérico |
| `claimed_at`, `released_at` | `int?` | §6 | Posse |
| `assignment_source` | enum `ORIGIN_SYSTEM` / `CLAIM` / `MANAGER` | §6 | Como a OS ganhou responsável |

No motor de campos, uma adição pequena: `Field.readonly: bool` — as horas de início e término do formulário de execução são pré-preenchidas e **não modificáveis** (RF-013), o que hoje não é expressável.

---

## 9. Núcleo 4 — Integração com o Apex

### 9.1 Entrada: o Apex chama `POST /forms` (D5)

Mesmo caminho já em produção com o Gaia. Ajustes necessários:

1. Aceitar `user_id` nulo quando `allow_unassigned_forms = true` (§6.3) — e continuar aceitando `user_id` preenchido no mesmo contrato, gravando `assignment_source = ORIGIN_SYSTEM`.
2. Aceitar `attributes`, `external_id`, `origin`, `service_type`, `occurred_at`, `scheduled_start_at`.
3. **Idempotência por `external_id` + `system`**: reenvio do Apex (ou retry de rede) não pode duplicar OS. Isso resolve simultaneamente o item bloqueado da criação offline no client (§5, item 2) — **a mesma implementação serve aos dois casos**.
4. Ingestão inicial: ~5.000 OS em estoque. Se a criação unitária se mostrar lenta demais no bootstrap, o mesmo controller aceita lote — decidir com números reais, não por antecipação.

### 9.2 Atualização de OS pelo Apex (RN-001, RN-002)

**Não existe endpoint de atualização de formulário pelo sistema origem.** A spec exige que mudanças de prioridade feitas no Apex reflitam de imediato no app. É preciso um `PATCH /forms/{form_id}` restrito ao sistema origem, aceitando `priority`, `attributes`, `expiration_date` e cancelamento pela origem — sem tocar em posse nem em respostas preenchidas.

### 9.3 Saída: o que o Informs envia

O `sync_forms_origin` (EventBridge a cada 5 min, com checkpoint por `system`, fila de erro e callback de falha) continua sendo o canal de saída. Ajustes:

- Segregar **abertura** (`created_by`, `origin`) e **fechamento** (`completed_by`, `completed_at`) no payload, para alimentar as tabelas "na equipe" e "concluído" (RF-036/RN-010).
- Incluir os eventos de posse do §6.4, se o Apex quiser refletir "quem está com a OS".
- Nova URL de destino para o system de Uberlândia — `OriginRepositoryApex` já resolve a URL por `system` (`_build_url`), então é configuração.

### 9.4 Pendência de contrato

A spec exige respeitar os protocolos do app atual gerado pelo Apex. Nomes de campos, tipos, autenticação e formato de payload **precisam ser conciliados com a equipe do Apex** antes da implementação — **Pendência P2**.

---

## 10. Núcleo 5 — Tempo real (D6)

**Ponto de partida**: já existe um serviço WebSocket próprio (`ws_server/`, FastAPI, hospedado no Railway, ~620 linhas), documentado no ADR-0018. Hoje ele transporta apenas pings de GPS: inspetores publicam, admins recebem fan-out.

### 10.1 Extensão do protocolo

Novo tipo de mensagem `form_event`, com `event_type` ∈ `created` / `claimed` / `released` / `assigned` / `started` / `completed` / `cancelled` / `updated`, e um payload enxuto (id, lat, lng, status, prioridade, dono).

**Salas** por `system` + valor da chave de particionamento de escopo (`bairro` em Uberlândia) — o mesmo mecanismo do §7, para que um executor da zona leste não receba eventos da cidade inteira.

### 10.2 Publicação

**Recomendação: DynamoDB Streams → Lambda publicadora → `POST /internal/publish` no `ws_server`.**

O motivo é de robustez, não de elegância: publicando a partir do stream, **qualquer** caminho de escrita emite o evento — os usecases, o sync, uma correção manual — sem que cada usecase precise lembrar de publicar. Acoplar a publicação a cada usecase é a variante que envelhece mal.

### 10.3 Consumo no client

Ao receber o evento, o client faz `setQueryData` **incremental** no cache do React Query, sem refetch da lista. É exatamente o que o RNF-004 pede: "atualizar pontos individuais sem re-renderizar o mapa inteiro". A infraestrutura de cache persistido já está pronta em `shared/offline/`.

### 10.4 Dívida conhecida a dimensionar

O ADR-0018 registra explicitamente: o `ConnectionRegistry` é **em memória, instância única**, dimensionado para ~15 inspetores. Uberlândia tem mais usuários simultâneos e passa a trafegar eventos de OS além de GPS. Antes de produção é preciso:

1. Estimar usuários simultâneos e eventos/segundo reais (a spec fala em "algumas centenas de aberturas e conclusões por dia" — fluxo baixo, o que é favorável).
2. Confirmar se uma instância aguenta; se não, migrar a presença para **Redis pub/sub**, caminho já previsto no ADR.

---

## 11. Núcleo 6 — Geofencing (D7)

Genérico e configurável por `system` (`SystemConfig.geofence_radius_m`; `null` = desligado, então **Gaia não é afetado**).

- **Cliente**: bloqueia a ação com aviso explícito antes de abrir o formulário de execução (RF-018, RNF-006/008). Funciona offline — a coordenada da OS está em cache.
- **Backend**: `start` e `submit` passam a aceitar `device_latitude`, `device_longitude` e `accuracy`. Se o system tiver raio configurado e a distância exceder `raio + accuracy`, responde **403** com erro tipado `OutsideGeofence`. Reaproveita `haversine_km`, já existente em `src/shared/helpers/functions/nearest_neighbor.py`.
- **Offline**: a coordenada enviada é a **capturada no momento do ato**, não a atual no momento da sincronização — a fila de mutations já carrega payload próprio por mutation, então isso é campo novo, não mecanismo novo.
- **Tolerância a GPS impreciso**: somar a `accuracy` reportada ao raio evita o modo de falha mais comum (o executor está no local, o GPS erra 80 m e a execução é negada). Comportamento exato a confirmar — **Pendência P1**.

---

## 12. Núcleo 7 — Perfil e métricas (RF-032, RF-033, RN-011)

`GET /profiles/me` passa a devolver `scope` e `role` (regiões de atuação na tela de perfil).

`GET /profiles/me/metrics` devolve, em janela móvel de 30 dias:
- OS concluídas **pelo usuário** — filtro por `completed_by` + `completed_at`;
- OS abertas **no escopo do usuário** — contagem por `created_at` sobre o escopo.

Sobre o cálculo: em 30 dias o volume é de algumas milhares de OS ("algumas centenas por dia"), o que torna a contagem sob demanda no GSI de escopo aceitável. Se medir mal em produção, o passo seguinte é um contador agregado atualizado pela Lambda de stream do §10 — mesma infraestrutura, sem componente novo.

---

## 13. Offline e conflito (RNF-003)

A spec deixa a política de conflito em aberto. Com o pool, ela deixa de ser opcional — dois executores offline poderiam reivindicar a mesma OS e um perderia trabalho já feito no merge.

**Política proposta:**

| Operação | Offline? | Racional |
| --- | --- | --- |
| `claim`, `release`, `assign` | ❌ **Exige conexão** | Exclusividade é intrinsecamente online. Uma reivindicação enfileirada é uma promessa que o servidor pode negar depois — e negá-la depois de o executor ter dirigido até o local e preenchido o formulário é o pior resultado possível. A UI desabilita a ação offline com aviso explícito. |
| `start`, `answer`, `submit`, `cancel` | ✅ Fila | Só o dono age, e a posse foi confirmada online **antes** — o conflito praticamente desaparece por construção. |

**Conflito residual** — o Gestor reatribui a OS enquanto o executor está offline com trabalho feito: o `submit` volta **403**. Tratamento: **não descartar** a mutation; marcá-la como conflito, preservar respostas e fotos localmente e apresentar tela de conflito com o motivo. A base existe (`describe-mutation-error.ts` e o limite de 5 tentativas que impede a fila de travar) — falta a categoria "conflito" e a tela.

O backend já tem a metade difícil: `update_form(..., expected_status=)` é concorrência otimista de verdade.

---

## 14. Escala (RNF-009)

Três problemas distintos, hoje mascarados pelo fato de o Gaia sempre consultar por dono:

1. **`Scan` da tabela inteira.** `get_all_forms` só usa índice quando há `user_id`; sem ele, `_scan_forms` varre tudo. Com o pool, a consulta principal passa a ser justamente "sem dono". **Solução: GSI esparso de pool.**

   ```
   GSI3PK = pool#{system}#{valor_da_chave_de_escopo}     # ex.: pool#UBERLANDIA#Santa Mônica
   GSI3SK = priority#{p}#created_at#{ts}
   ```

   O atributo `GSI3PK` **só existe enquanto `user_id` é nulo** — uma OS direcionada nunca entra no índice, e uma devolvida ao pool volta a entrar. Ao reivindicar, o atributo é removido e o item **sai do índice sozinho** — o pool fica sendo exatamente o conteúdo do índice, sem filtro nem varredura. É o desenho mais barato possível para "quem clicar tira da lista dos outros".

   Restrição aceita: a chave de particionamento de escopo (`scope_partition_key`) admite **um valor por OS**. As demais chaves de `attributes` são filtro pós-query, sobre um conjunto já pequeno.

2. **Payload pesado no mapa.** Devolver o formulário completo (com seções, campos e integridade de arquivos) para 10.000 pins é inviável. **Solução:** projeção enxuta — `GET /forms/pins` devolvendo apenas `id`, `lat`, `lng`, `status`, `priority`, `external_id`. A ficha completa continua sendo carregada sob demanda ao abrir a OS.

3. **Recarga após período offline.** Já resolvida no backend: `get_forms_updated_since` sobre o GSI2 (`system#{system}` + `updated_at`) — falta expor como parâmetro de delta em `GET /forms` e consumir no client.

No cliente, o clustering do MapLibre já está ligado; o teste de carga com 10.000 pontos ainda precisa ser feito.

---

## 15. Fases de entrega

Cada fase é entregável e testável isoladamente; nenhuma quebra o contrato Gaia.

| Fase | Conteúdo | Entrega |
| --- | --- | --- |
| **0 — Fundação** | `SystemConfig` por contrato; campos novos de `Form` (§8); idempotência por `external_id`; `PUT /profiles/{user_id}`; de-para de contrato com o Apex | Uberlândia consegue **criar** OS no Informs |
| **1 — Pool e posse** | `user_id` opcional; `claim`/`release`/`assign` com condicional atômica; histórico; GSI3 esparso; `scope=pool` em `GET /forms` | **A feature que motiva o contrato** |
| **2 — Escopo e RBAC** | `attributes` + `Profile.scope`; papéis Gestor/Fiscal; gate de "Gerar OS em campo"; perfil exibindo regiões | RN-001 e a seção 4 da spec |
| **3 — Tempo real** | DynamoDB Streams → publicadora → `ws_server`; salas por escopo; consumo incremental no client | RN-006, RNF-004, RF-031 |
| **4 — Geofencing e campos da spec** | Raio por system, validação cliente + backend; origem, nº da OS, tipo de serviço, datas; `Field.readonly` | RF-018, RF-008/009, RN-004 |
| **5 — Escala e mapa** | `GET /forms/pins`; delta incremental; camada satélite; centralizar; heading; busca por logradouro | RNF-009, RF-021/022/025/026 |
| **6 — Perfil, métricas e acabamento** | Métricas de 30 dias; retenção do verde; fluxo de 2 passos de "Gerar OS"; passada de UI de campo | RF-028/029/033, RN-007, RNF-006/007/008 |

As fases 0 a 2 são o caminho crítico e têm dependência dura da definição do contrato com o Apex (**Pendência P2**).

---

## 16. Pendências e decisões em aberto

| # | Pendência | Quem decide | Bloqueia |
| --- | --- | --- | --- |
| **P1** | Raio de geofencing e comportamento com GPS impreciso/indoor — a spec manda replicar o que o Curci já implementou no app atual | Curci / Apex | Fase 4 |
| **P2** | Contrato de dados do Apex: nomes de campos, tipos, autenticação, formato dos payloads de entrada e saída | Intelicity + Apex | Fases 0–2 |
| **P3** | ⚠️ **Divergência**: por D2, a OS reivindicada some **também** para Gestor e Fiscal, mas a spec (seção 4) dá a eles "cidade toda". Confirmar com o gestor | Gestor Intelicity | Fase 1 |
| **P4** | Login: manter Cognito Hosted UI (redirect) ou construir tela própria de usuário/senha com "lembrar" e "esqueci minha senha" (RF-001/003) | Intelicity | Fase 6 |
| **P5** | Ao devolver a OS ao pool, as respostas e fotos já preenchidas são preservadas ou descartadas? **Recomendação: preservar**, marcando no histórico quem iniciou — descartar destrói trabalho e evidência | Gestor Intelicity | Fase 1 |
| **P6** | RN-007 (verde por ≥ 7 dias): a OS concluída fica visível só para quem executou ou para todo o escopo? | Gestor Intelicity | Fase 6 |
| **P7** | Capacidade do `ws_server` (instância única, presença em memória — ADR-0018) para o volume de Uberlândia | Equipe técnica | Fase 3 |
| **P8** | Reverse geocoding para o passo 1 de "Gerar OS em campo" (RF-028): provedor, custo e comportamento offline | Equipe técnica | Fase 6 |
| **P9** | Fonte da lista de logradouros e bairros para os autocompletes (RF-006, RF-022) — provavelmente o Apex | Apex | Fase 5 |
| **P10** | "Início esperado" e "término esperado" (RF-008): campos novos ou reuso de `expiration_date`? | Apex | Fase 0 |
| **P11** | Uma OS **direcionada** pelo sistema origem pode ser devolvida ao pool pelo próprio executor, ou só o Gestor/Fiscal pode redistribuí-la? **Recomendação: permitir ao executor**, porque o motivo de devolver ("não vou conseguir fazer esta") independe de como a OS chegou — registrando o rompimento do direcionamento no histórico e no sync | Gestor Intelicity | Fase 1 |

---

## 17. Riscos

| Risco | Impacto | Mitigação |
| --- | --- | --- |
| Contrato do Apex definido tarde | Trava as fases 0–2, que são o caminho crítico | Priorizar P2; até lá, desenvolver contra os mocks (`origin_repository_mock`) |
| `ws_server` não aguentar o volume | RN-006 não atendido em produção | P7 antes da fase 3; caminho de Redis pub/sub já previsto no ADR-0018 |
| Reivindicação offline pedida depois pelo cliente | Reabre o desenho de conflito | Política de §13 registrada agora, com o motivo — decisão consciente, não omissão |
| Regressão no Gaia | Contrato em produção | `allow_unassigned_forms`, `scope` vazio e `geofence_radius_m` nulo preservam o comportamento atual por construção; a suíte de 107 arquivos de teste é a rede de segurança |
| 10.000 pins no PWA | RNF-009 | Teste de carga na fase 5, antes do piloto; clustering já ligado |
| Divergência P3 descoberta em homologação | Retrabalho de visibilidade | Confirmar com o gestor antes da fase 1 |
