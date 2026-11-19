# Débito técnico

Itens conhecidos do Informs (este repositório e o `informs-front`), com o motivo de existirem e o que resolveria cada um. É o único registro de débito técnico do Informs: o `informs-front` não tem arquivo próprio.

Vêm de três levantamentos:

- **11/11/2026** (DT-01 a DT-05): revisão da arquitetura Informs × Apex, lendo o código de `origin/dev` (`ab19eea`, merge do #108) contra as ADRs.
- **13/11/2026** (DT-06 a DT-13 e DT-17 a DT-36): levantamento dos dois repositórios, publicado fora do git e trazido para cá em 19/11. Os itens dele foram renumerados; a coluna ou linha **Origem** diz o número original (DT-1 a DT-8, N1 a N20).
- **18 e 19/11/2026** (DT-14 a DT-16): revisão da sincronização e dos relatos de campo de Uberlândia.

Cada item cita o arquivo e a linha da evidência. Onde algo foi conferido em ambiente (banco, S3 ou métricas de DEV), o texto diz a data. O resto foi lido no código.

A numeração segue a ordem de registro, não de risco: a severidade está no índice e na linha de cada item.

**Estado de cada item:** a linha **Estado**, logo abaixo do título, diz se está aberto, parcial ou resolvido. Item resolvido continua no arquivo: o parágrafo **Resolvido (data)** registra como foi resolvido. Só se marca resolvido o que foi conferido no código ou no ambiente.

**O que é débito técnico aqui:** algo no código ou no modelo de dados que se sabe diferente do que a ADR diz ou comprometido, com o motivo e a solução. Não é débito, e fica em outro lugar:

| O quê | Onde |
| --- | --- |
| Decisão de negócio ou resposta de outro time ainda pendente | seção "Dependências externas e decisões pendentes", no fim deste arquivo |
| Passo de implantação (deploy, variável do CDK) | `README.md` e a ADR que o define |

## Índice

| ID | Título | Severidade | Estado | Repositório |
| --- | --- | --- | --- | --- |
| DT-01 | O estado `SENT` existe na ADR e nos contratos, mas nenhum caminho o grava | não atribuída | aberto | back |
| DT-02 | `FAILED` e `IDLE` do `SyncState` nunca são gravados | não atribuída | aberto | back |
| DT-03 | Lote fora da trava volta `SKIPPED_NON_PROD` e conta como enviado | não atribuída | aberto | back |
| DT-04 | O número da rua não vem do geocode reverso em parte dos pontos | não atribuída | aberto | back e front |
| DT-05 | Sair de um grupo não limpa o pool no cache do aparelho | não atribuída | aberto | back e front |
| DT-06 | O sync só sabe que falhou se o Apex disser | alta | aberto | back |
| DT-07 | O app baixa todos os formulários abertos, e o download se perde fácil | alta | aberto | back e front |
| DT-08 | A operação real de Uberlândia roda no ambiente de DEV | crítica | aberto | back e front |
| DT-09 | `origin` é gravado mas não serve para nada; `created_by` não diz o canal | baixa | parcial | back e front |
| DT-10 | Formulário novo ou alterado só chega aos aparelhos no próximo polling | alta | aberto | back e front |
| DT-11 | O mapa pesa com muitos pins | média | aberto | front |
| DT-12 | Mudança no usuário demora a valer, e desativar não bloqueia o campo | alta | aberto | back e front |
| DT-13 | Erro no back e no front não fica registrado em lugar nenhum | crítica | aberto | back e front |
| DT-14 | Iniciar ou enviar repetido pela fila offline trava o formulário | alta | aberto | back e front |
| DT-15 | Escritas do formulário sem versão; `release` grava sem condição | alta | aberto | back |
| DT-16 | Anexo enviado na criação sobe uma vez só, sem fila | alta | aberto | front |
| DT-17 a DT-36 | Itens do levantamento de 13/11 ainda sem detalhamento (tabela no fim) | crítica a baixa | aberto (DT-36 parcial) | back e front |

---

## DT-01 — O estado `SENT` do formulário existe na ADR e nos contratos, mas nenhum caminho o grava

**Estado:** aberto.

**Onde:** `src/modules/sync_forms_origin/app/sync_forms_origin_usecase.py`; `src/shared/domain/enums/form_status_enum.py:8`; `docs/adr/0008-ciclo-de-vida-do-formulario.md`.

**Problema:** a ADR-0008 define a transição `COMPLETED → SENT`, a cargo do módulo `sync_forms_origin`, "envio ao sistema de origem com sucesso". O código do sync grava o `SyncState` e a fila de erros (`SyncErrorForm`), mas não altera o status do formulário. Uma busca por `FormStatus.SENT` e `status=` em `sync_forms_origin` e nos repositórios não acha nenhuma escrita; `SENT` só aparece no enum, nos contratos (`template_versioning_contract.py:7`, `schemas/form.py:10`) e em `reconcile_form_files_usecase.py:61` (`RECONCILED_STATUSES = (COMPLETED, SENT)`).

**Consequência:** o status do formulário não diz se ele foi ao Apex. Quem consome a API vê `COMPLETED` para o que foi enviado e para o que não foi. A reconciliação cobre `SENT` por contrato, mas na prática só enxerga `COMPLETED`. A ADR descreve um ciclo que o sistema não cumpre.

**Resolução:** decidir entre duas saídas, e registrar a decisão numa ADR:

1. Gravar `SENT` no lote com sucesso real. O envio fora da trava (`SKIPPED_NON_PROD`, ver DT-03) **não** pode virar `SENT`: o formulário não foi ao Apex.
2. Emendar a ADR-0008 e os contratos para tirar `SENT` e dizer onde o envio é rastreado (hoje, só no `SyncState` e na fila de erros).

**Mitigação atual:** nenhuma. O checkpoint por lote e a fila de erros garantem a recuperação, não a visibilidade por formulário.

---

## DT-02 — `FAILED` e `IDLE` do `SyncState` são válidos e nunca gravados; execução que cai fica `RUNNING`

**Estado:** aberto.

**Onde:** `src/shared/domain/entities/sync_state.py:21` (`VALID_STATUS = {"IDLE", "RUNNING", "COMPLETED", "FAILED"}`); `sync_forms_origin_usecase.py:167`, `:354` (`RUNNING`) e `:442` (`COMPLETED`).

**Problema:** o use case grava `RUNNING` no início e a cada lote e `COMPLETED` no fim. Não há escrita de `FAILED` nem de `IDLE` em `src` (busca por `status="FAILED"` e `status="IDLE"` sem resultado). Uma execução interrompida (timeout da Lambda, de 900 s, ou erro não tratado) não passa pelo bloco final, então o estado fica `RUNNING`.

**Consequência:** `RUNNING` não distingue "em andamento" de "morreu no meio". Não há como alarmar por estado: só olhando o `started_at` antigo. O checkpoint não é afetado (só avança no bloco final, e em execução parcial volta ao anterior: `:433`), então não perde dado; perde-se o sinal operacional.

**Resolução:** gravar `FAILED` com `ended_at` num `except`/`finally` do use case, ou remover `IDLE` e `FAILED` do conjunto válido para a entidade não prometer o que não faz. Em qualquer caso, um alarme sobre `RUNNING` mais velho que o timeout da Lambda.

**Mitigação atual:** a janela de uma hora e o checkpoint por lote (ADR-0010) fazem a próxima execução retomar sem perda.

---

## DT-03 — Lote fora da trava volta `SKIPPED_NON_PROD`, conta como enviado e o checkpoint avança

**Estado:** aberto. A decisão de não enviar fora de PROD é deliberada (ADR-0021, incidente de 08/09/2026); o que está aberto é como o resultado é registrado.

**Onde:** `src/shared/infra/repositories/origin_repository_apex.py:221` (`return True, SUCCESS_STATUS_CODE, "SKIPPED_NON_PROD"`); `sync_forms_origin_usecase.py:245` (`_is_success_response`); ADR-0021.

**Problema:** quando a origem não está habilitada (trava global desligada e a origem fora de `APEX_SYNC_ENABLED_ORIGINS`), o repositório devolve sucesso com o motivo `SKIPPED_NON_PROD`. O use case trata como enviado: o lote entra na contagem de enviados e o checkpoint avança.

**Consequência:** em DEV e HML o resultado do sync mostra "enviados" que não foram ao Apex. Os números de DEV não dizem se o envio funciona. Ao ligar uma origem depois, o que já passou pelo checkpoint como `SKIPPED_NON_PROD` não é reenviado: é preciso mexer no checkpoint ou reenviar à mão.

**Resolução:** devolver um resultado próprio (`skipped`) separado de sucesso, contado à parte no resultado e na métrica, e decidir por ADR se o checkpoint avança nesse caso. Manter o checkpoint como está é coerente com a ADR-0021; o que muda é a contagem e o `SENT` do DT-01.

**Mitigação atual:** o motivo `SKIPPED_NON_PROD` vai no log do lote.

---

## DT-04 — O número da rua não vem do geocode reverso em parte dos pontos

**Estado:** aberto.

**Onde:** `src/shared/infra/repositories/reverse_geocoder_revgeo.py` (`parse_nominatim`); etapa Local do front (campo "S/N").

**Problema:** o Nominatim (OpenStreetMap) só devolve `house_number` quando o ponto cai sobre um endereço mapeado. Em ponto de via, vem a rua e a cidade e o número fica vazio. Observado no E2E local de 11/11 com a chave real: pin na Rua Arizona, São Paulo, devolveu rua e cidade, número vazio.

**Consequência:** o formulário pode ser criado sem número. Para serviço de campo (buraco, ramal) costuma bastar; integração ou relatório que exige número recebe vazio ou "S/N".

**Resolução:** decidir entre (a) aceitar "S/N" como valor válido e registrar na ADR da criação em passos; (b) um geocoder com numeração por interpolação atrás do `revgeo`; (c) estimar o número mais próximo na via a partir de pontos vizinhos.

**Mitigação atual:** o campo é editável e a pessoa digita o número.

---

## DT-05 — Sair de um grupo não limpa o pool no cache do aparelho pelo delta incremental

**Estado:** aberto.

**Onde:** `GET /forms?scope=pool&updated_after=` (`get_all_forms_usecase.py`); `docs/adr/0022-grupos-do-sistema.md`.

**Problema:** quem sai de um grupo deixa de ver a OS do grupo no servidor (provado no E2E: some do pool e o `claim` volta 403). O delta não a coloca em `removed_from_pool`, porque a OS não mudou (`updated_at` igual): o que mudou foi o vínculo pessoa↔grupo. A ADR-0022 define quem vê, abre e assume, mas não diz o que acontece com o cache do aparelho.

**Consequência:** o aparelho mantém a OS no cache até a sincronização completa (a cada 6 h, `FULL_SYNC_INTERVAL_MS` em `shared/queries/forms-delta.ts` do `informs-front`) e pode exibi-la e abri-la offline nesse intervalo. Ao tentar assumir, o servidor nega.

**Resolução:** decidir entre (a) aceitar e documentar o intervalo na ADR-0022; (b) o delta do pool devolver como removida toda OS de grupo que a pessoa não tem mais, comparando com os grupos atuais. O vínculo já é lido em `GET /forms?scope=pool`, então o custo extra é pequeno.

**Mitigação atual:** sincronização completa a cada 6 h e `claim` negado no servidor. Corrigido em 19/11: o texto dizia "de hora em hora". O DT-10 trata o mesmo atraso para formulários que saem de "minhas".

---

## DT-06 — O sync só sabe que falhou se o Apex disser

**Estado:** aberto. **Severidade:** alta. **Origem:** levantamento de 13/11 (DT-1).

**Onde:** `src/shared/infra/repositories/origin_repository_apex.py`; `src/modules/sync_forms_origin/app/sync_forms_origin_usecase.py`; `src/modules/sync_forms_origin_callback/`; `iac/iac/lambda_stack.py:480-494`.

**Problema:** só HTTP 200 conta como sucesso, e o corpo da resposta é ignorado (`failed_form_ids`, `gravados`). 202 e 204 contam como falha. A fila de erros não tem limite de tentativas nem estado final. Ninguém é avisado de falha, e a reconciliação compara Dynamo com S3, não com o Apex.

**Consequência:** um formulário que o Apex perdeu com resposta 200 sai da fila e o checkpoint avança. Não dá para saber se um formulário chegou ao Apex. Timeout pode gerar reenvio.

**Resolução:** combinar com o Apex um corpo de resposta por formulário; tratar qualquer 2xx igual; limitar as tentativas e criar o estado "não entregue"; alertar pelo Kuma; reconciliar Informs × Apex. Ver também DT-01 (`SENT`), DT-02 (`FAILED`), DT-03 (`SKIPPED_NON_PROD`), DT-18 (callback sem autorização) e DT-23 (contrato igual ao formato do banco).

**Mitigação atual:** nenhuma além do checkpoint por lote e da fila de erros.

---

## DT-07 — O app baixa todos os formulários abertos, e o download se perde fácil

**Estado:** aberto. **Severidade:** alta. **Origem:** levantamento de 13/11 (DT-2), ampliado em 19/11.

**Onde:** back: `src/modules/get_all_forms/app/get_all_forms_usecase.py` (`POOL_DEFAULT_LIMIT = 200`). Front: `shared/queries/use-forms.ts`, `shared/queries/forms-delta.ts:66`, `shared/queries/freshness.ts`, `shared/offline/query/create-persister.ts`, `clients/web/src/lib/storage-scope.ts`.

**Problema:**

- **Volume.** Cada aparelho baixa o pool inteiro. Em 19/11, o pool de `UBERLANDIA` em DEV tinha **6.326 formulários abertos, 22,6 MB em JSON** (mediana de 3,7 KB por formulário), em 32 páginas de 200. "Minhas" não filtra por status nem prazo e traz o histórico.
- **Tudo ou nada.** A sincronização só grava quando todas as páginas chegam (`forms-delta.ts`). Uma página que falha descarta as anteriores, e a próxima tentativa recomeça da primeira.
- **Trocar de tela cancela o download.** A busca só fica montada na Lista, no Mapa e no detalhe (`useForms`). A tela inicial do papel Fiscal em Uberlândia é Criar. O `queryFn` repassa o `signal` ao `fetch`, então sair dessas telas no meio cancela a carga.
- **Quem cria não vê o que criou.** Depois do `POST /forms`, o formulário só entra na lista na próxima sincronização do pool, que é a que se perde pelos itens acima.
- **A falha é silenciosa.** Se o pool falha, a lista própria aparece normal e o pool fica faltando (`use-forms.ts:213`).
- **Cache num bloco só.** O persister grava todo o cache do React Query como um único texto no IndexedDB, regravado a cada mudança (throttle de 3 s) e lido inteiro na abertura. Com o pool acima, são mais de 22 MB.
- **Carga completa recorrente:** a cada 6 h (`FULL_SYNC_INTERVAL_MS`) e quando o cache tem mais de 3 dias (`maxAge`).

**Consequência:** em 18 e 19/11 equipes de Uberlândia relataram formulário que não aparece no mapa, nem para quem criou, enquanto o gestor vê. No back não houve erro: nas 27 h anteriores a 19/11 10h, nenhuma Lambda de DEV registrou erro ou throttle, a listagem levou no máximo 1,9 s e o API Gateway teve ~1% de 4xx. A causa provável está no app. **Hipótese não confirmada** para o pico: a versão web de 18/11 passou a guardar o cache por usuário (`storage-scope.ts`), e onde a migração do cache antigo não pegou, o aparelho teve de baixar tudo de novo. Confirmar no PostHog com `forms_list_synced` (`mode`) e `forms_list_sync_failed` (`scope = pool`).

**Resolução:** curto prazo no front: o download continua ao trocar de tela; o formulário criado entra no cache na hora; a carga guarda o progresso por página e retoma de onde parou; a falha do pool aparece; o app só bloqueia com barra de progresso quando o aparelho não tem lista nenhuma. Estrutural: o aparelho recebe só o pool da região (ou por distância) e o resto sob demanda; a lista traz um resumo e o formulário completo vem ao abrir ou pegar; o cache é guardado por formulário. Medir antes e depois com 1k, 5k e 10k formulários. Ver também DT-21 (marcadores de outros no delta) e DT-22 (token de paginação).

**Mitigação atual:** botão Sincronizar e intervalo mínimo de 60 s entre buscas.

---

## DT-08 — A operação real de Uberlândia roda no ambiente de DEV

**Estado:** aberto. **Severidade:** crítica. **Origem:** levantamento de 13/11 (DT-3).

**Onde:** `.github/workflows/CD.yml`; `iac/iac/dynamo_stack.py:17`; `src/shared/infra/repositories/origin_repository_apex.py:14-21`; `src/shared/environments.py:141-151`; ADR-0021; `README.md`. Front: `package.json:5`, `tracking-store.ts:53`.

**Problema:** Uberlândia opera no DEV, com envio real ao Apex. O DEV é implantado à mão e o CD está parado; em 22/10 isso derrubou o ambiente. `homolog` e `prod` estão paradas em 31/08/2026 (`origin/prod` em `fd4cf64`), e a `prod` tem 20 dos 44 módulos do `dev` (conferido em 19/11). As tabelas do DEV usam `RemovalPolicy.DESTROY`. O endereço do Apex de produção é fixo em todos os ambientes, e em 08/09 o DEV enviou formulários de teste ao Apex real. No front, os tipos vêm da API de DEV, o WebSocket cai em `informs-ws-dev` e o mapeamento do Amplify só existe no console.

**Conferido em 19/11:** os tablets de campo de Uberlândia (`obrastablet1` a `obrastablet9` e os logins de equipe) criam e concluem formulários no banco de DEV, então o app de campo aponta para DEV. Falta confirmar se o `POST /forms` do Apex também aponta para DEV.

**Consequência:** dado real e de teste misturados; todo merge em `dev` vai direto ao uso real; um `cdk destroy` pode apagar dado de cliente; promover para `prod` soltaria dois meses e meio de mudanças de uma vez.

**Resolução:** ADR de ambientes (dev → homolog → prod); deploy reproduzível (script ou CodeBuild, por causa do plano Free do Actions), com OIDC no lugar da chave fixa (DT-27); stack PROD para Uberlândia com tabelas `RETAIN` e migração dos dados; ambiente de teste no Apex ou `APEX_URL_<ORIGEM>` por ambiente; Amplify e EAS configurados no repositório.

**Mitigação atual:** envio ao Apex ligado por padrão só em PROD (ADR-0021); PITR nas tabelas.

---

## DT-09 — `origin` é gravado mas não serve para nada; `created_by` não diz o canal

**Estado:** parcial. **Severidade:** baixa. **Origem:** levantamento de 13/11 (DT-4).

**Onde:** `src/shared/domain/enums/form_origin_enum.py`; `src/modules/create_form/app/create_form_controller.py`; `contracts/base.py:12`. Front: `create.tsx`.

**Problema:** `origin` (`CITIZEN`, `AI`, `FIELD`, `ORIGIN_SYSTEM`) é gravado e enviado ao Apex, mas nenhuma regra, filtro ou permissão o usa, e só as integrações o preenchem. `created_by` vem do `sub` do token, então integração aparece como admin, e o app mostra o UUID. O `create_form` não grava `assignment_source=ORIGIN_SYSTEM`.

**Consequência:** qualquer chamador declara o campo sem validação. Três nomes parecidos causaram o 400 do header `Origin`. Não dá para auditar o canal de origem.

**Resolução:** ADR fixando o significado e renomeando para `demand_source`; `created_via` calculado no servidor a partir do token; gravar `assignment_source`; mostrar o nome de quem criou.

**Mitigação atual:** o 400 foi corrigido no #113, em `dev` desde 12/11. A `prod` ainda tem o bug, porque não recebe nada desde 31/08 (DT-08). Falta confirmar se o Apex envia ou lê `origin`.

---

## DT-10 — Formulário novo ou alterado só chega aos aparelhos no próximo polling

**Estado:** aberto. **Severidade:** alta. **Origem:** levantamento de 13/11 (DT-5).

**Onde:** front: `shared/queries/freshness.ts`, `shared/queries/forms-delta.ts:66`, `vite.config.ts`. Back: `ws_server/main.py`, `iac/iac/dynamo_stack.py:32`. Especificação: RNF-004, RN-006, §10.

**Problema:** não existe aviso do servidor quando um formulário muda. Com o app aberto, a atualização leva até 2 min; ao voltar ao app, é imediata se o dado tem mais de 60 s; em segundo plano, não atualiza. Formulário liberado ou atribuído a outra pessoa leva até 6 h para sair de "minhas", porque o delta de "minhas" não manda marcador de saída (`get_all_forms_usecase.py`, ramo `scope=mine`). A mudança de grupo é o DT-05. O DynamoDB Stream da tabela de formulários está ligado (`NEW_IMAGE`) sem consumidor neste repositório. A especificação pede propagação em poucos segundos.

**Consequência:** em Uberlândia, onde quase tudo é pool, quem vê o pool tenta pegar formulário que já tem dono e recebe "já pego". Quem teve o formulário liberado pode preenchê-lo e ter o envio recusado.

**Resolução:** aviso em tempo real por sistema (DynamoDB Streams → Lambda → AppSync Events), em que o aviso só diz "mudou" e o delta continua sendo a fonte da verdade; delta único por sistema, com marcador de saída e com a impressão do acesso da pessoa para resolver o DT-05. Web Push para app fechado fica fora (no iOS, só com o PWA instalado). Ver DT-29 (`ws_server` não escala).

**Mitigação atual:** polling de 2 min, atualização ao voltar ao app, botão Sincronizar, carga completa a cada 6 h.

**Corrigido desde o levantamento:** "ação com erro na fila offline trava a atualização" deixou de valer em 16/11 (informs-front `43db715`): a lista atualiza sempre, e as ações pendentes são reaplicadas por cima (`withPendingMutations`).

---

## DT-11 — O mapa pesa com muitos pins

**Estado:** aberto. **Severidade:** média (hipótese, sem medição). **Origem:** levantamento de 13/11 (DT-6).

**Onde:** front: `forms-marker-cluster.tsx:142-153, 176, 219`, `map.tsx`.

**Problema (suspeitas, da mais à menos provável):** cada pin e cluster é um elemento HTML (`<Marker>`) acima do zoom 16; o índice do Supercluster é refeito a cada mudança da lista; o enquadramento fica no estado da página, que re-renderiza ao mover o mapa.

**Consequência:** lentidão no mapa, ainda não medida. O pool de Uberlândia em DEV tem 6.326 formulários abertos (19/11), todos com coordenada.

**Resolução:** medir com 1k, 5k e 10k formulários sintéticos (perfil do React e FPS em celular de campo); trocar os `<Marker>` por camada GeoJSON do MapLibre com cluster nativo; refazer o índice só quando `id` ou `updated_at` mudarem; tirar o enquadramento do estado da página. Diminuir o pool no aparelho (DT-07) também reduz isto.

**Mitigação atual:** clusters recalculados só quando o mapa para de mover.

---

## DT-12 — Mudança no usuário demora a valer, e desativar não bloqueia o campo

**Estado:** aberto. **Severidade:** alta. **Origem:** levantamento de 13/11 (DT-7).

**Onde:** back: `src/shared/domain/services/access_control.py`, `start_form`, `submit_form`, `cancel_form`, `claim_form`, `ws_server/auth.py`. Front: `app-profile-store.ts`, `shared/permissions/ability.ts`.

**Problema:** papel e ações valem na API na hora, mas no app só no próximo login, com o perfil em cache (pode levar dias). A permissão de rastreamento vale só ao abrir o WebSocket. Grupo vale na API na hora e no app em até 6 h (DT-05). A configuração do app leva até ~5 min. O acesso ao sistema muda quando o token renova (hipótese: ~1 h). **Perfil desativado:** o login dá 403, mas listar, iniciar, enviar, cancelar e pegar formulário sem grupo não checam `active`, e a falha do login mantém o cache.

**Consequência:** uma pessoa desativada continua em campo até o token vencer ou até ser tirada do grupo `FORMULARIOS` do Cognito. Ação nova só aparece depois de sair e entrar.

**Resolução:** checar `active` num guard comum a todos os endpoints de campo (urgente); buscar o perfil de novo ao voltar ao app e em intervalo; aviso de "perfil mudou"; reavaliar as conexões do WebSocket. Falta confirmar se o `@intelicity/gates-auth` avisa ao renovar o token e se o service worker entrega `/app-config` antigo quando a API demora.

**Mitigação atual:** nenhuma.

---

## DT-13 — Erro no back e no front não fica registrado em lugar nenhum

**Estado:** aberto. **Severidade:** crítica. **Origem:** levantamento de 13/11 (DT-8).

**Onde:** back: `controller_error_handler.py`, `*_presenter.py`, `iac/iac/lambda_stack.py:460,510`, `ws_server/`. Front: `routes/`, `query-client.ts`.

**Problema (back):** o handler devolve 500 com a mensagem interna (`str(err)`) e não loga. 39 das 43 Lambdas não têm logger no presenter. X-Ray só no sync e no reconcile; API Gateway sem tracing nem access log; Kuma só no reconcile; sem `correlation_id`; o `ws_server` loga só no stdout. **Problema (front):** sem `errorComponent`, error boundary, handler global, `onError` no React Query nem SDK de erros.

**Consequência:** erro só aparece quando o técnico reclama. O 500 expõe detalhe interno. Não há como medir erros nem validar correções. Em 19/11, a investigação dos relatos de Uberlândia dependeu de métricas agregadas do CloudWatch, sem log das requisições.

**Resolução:** `logger.exception` no handler comum, com módulo e `correlation_id`; 500 genérico com id para suporte; access log no API Gateway; error boundary e handler global no app; log estruturado no `ws_server`. A ferramenta (SigNoz ou Sentry; PostHog no front) ainda não foi escolhida.

**Mitigação atual:** desde 16/11 o app manda ao PostHog eventos de sincronização (`forms_list_synced`, `forms_list_sync_failed`) e da fila offline (`offline_mutation_synced`, `offline_mutation_failed`), com tipo, status e tempo (informs-front `43db715`). Cobre a sincronização, não os erros em geral.

---

## DT-14 — Iniciar ou enviar repetido pela fila offline trava o formulário

**Estado:** aberto. **Severidade:** alta. **Origem:** revisão de 18/11.

**Onde:** back: `src/shared/domain/entities/form.py:375` (`start`), `src/modules/submit_form/app/submit_form_usecase.py`, `submit_form_controller.py:53` e `start_form_controller.py:43` (`ForbiddenAction` → 403). Front: `shared/offline/sync/submit-error-helpers.ts:63-68`, `shared/offline/stores/create-offline-sync-store.ts:190`.

**Problema:** com sinal ruim, o servidor aplica a ação e a resposta se perde; a fila reenvia. O `start` repetido responde 403 "não está aberto para início"; o `submit` repetido responde 403 "não está em andamento". O front só reconhece "já enviado" em 400 ou 409, então trata o 403 como recusa definitiva e bloqueia o formulário na fila. Conflito de concorrência também vira 403 ("Formulário foi atualizado por outra operação", `form_repository_dynamo.py:405`), sem como o cliente separar de falta de permissão.

**Consequência:** formulário vermelho e travado no aparelho, e o envio seguinte dele nunca sai.

**Resolução:** repetir não é erro: `start` de formulário já em andamento pela mesma pessoa e `submit` de formulário já concluído por ela respondem 200 (com URLs novas se faltar anexo). Conflito responde 409 com `code` estável e o formulário atual no corpo; a fila aplica o formulário recebido e sai do vermelho.

**Mitigação atual:** nenhuma.

---

## DT-15 — Escritas do formulário sem versão; `release` grava sem condição

**Estado:** aberto. **Severidade:** alta. **Origem:** revisão de 18/11.

**Onde:** `src/shared/infra/repositories/form_repository_dynamo.py`: `release_form` (`:473`, sem `ConditionExpression`), `update_form` (`:394`, condiciona só `status`).

**Problema:** o `release_form` lê o formulário, confere no use case que não está finalizado e grava sem condição. Se o dono envia entre a leitura e a escrita, a liberação devolve ao pool um formulário concluído e apaga as respostas. O `update_form` condiciona só o status, não o dono. Não há campo de versão no item.

**Consequência:** janela pequena, mas com perda de trabalho quando acontece.

**Resolução:** campo `version` que sobe a cada escrita; toda escrita condicionada à versão lida e, quando couber, ao dono (itens antigos: `attribute_not_exists(version) OR version = :v`); conflito responde 409 (DT-14).

**Mitigação atual:** só o ADMIN do sistema (`forms.release`) libera formulário de outra pessoa, o que torna o caso raro.

---

## DT-16 — Anexo enviado na criação sobe uma vez só, sem fila

**Estado:** aberto. **Severidade:** alta. **Origem:** revisão de 19/11.

**Onde:** front: `clients/web/src/routes/_authenticated/_tabs/create.tsx:327-417` (`uploadInformationFiles`).

**Problema:** o app cria o formulário, que já nasce apontando para o arquivo, e só depois faz o PUT no S3, uma vez, sem fila offline e sem nova tentativa. Se falha, mostra um toast e segue.

**Consequência:** o formulário aponta para um arquivo que não existe. Em 19/11, dos 252 arquivos referenciados por formulários concluídos de `UBERLANDIA` alterados nas 26 h anteriores, **11 não existiam no S3**, todos do tipo `information_field` (anexo da criação). Nenhuma foto do preenchimento faltava, porque elas passam pela fila offline.

**Resolução:** o upload do anexo da criação entra na fila offline, com o arquivo guardado no aparelho e novas tentativas; se o link expirar, pedir outro ao back, como o `refresh_presign` faz no envio. O `reconcile_form_files` continua como rede de segurança.

**Mitigação atual:** toast na hora da falha.

---

## DT-17 a DT-36 — Itens do levantamento de 13/11 ainda sem detalhamento

Vieram do levantamento de 13/11 (N1 a N20) com problema e sugestão, mas sem resolução detalhada. Todos estão **abertos**, menos o DT-36, **parcial**: a parte deste arquivo foi corrigida nesta revisão. Quando um deles for detalhado, ganha seção própria acima.

| ID | Levantamento | Título | Severidade | Onde | Problema | Encaminhamento |
| --- | --- | --- | --- | --- | --- | --- |
| DT-17 | N1 | Admin vê a posição de técnicos de todos os sistemas | Crítica | `ws_server/presence.py`, `main.py`, `auth.py` | Broadcast global para admins; qualquer admin ou `tracking.view` basta | Primeiro da fila |
| DT-18 | N2 | Callback do sync sem autorização | Alta | `src/modules/sync_forms_origin_callback/app/` | Qualquer usuário logado põe ids na fila; o 404 revela se um id existe | Junto do DT-06 |
| DT-19 | N3 | Template sem trava de concorrência | Alta | `template_repository_dynamo.py:44,125` | Salvamento simultâneo sobrescreve a versão do outro | Próprio |
| DT-20 | N4 | Front sem CI | Alta | informs-front `deploy-play-store.yml` | Testes e E2E não rodam no PR | Próprio; até lá, rodar localmente |
| DT-21 | N5 | Delta do pool manda marcador de formulário que a pessoa não pode ver | Média | `get_all_forms_viewmodel.py:90` | Marcadores de formulários de grupos alheios | Junto do DT-07 |
| DT-22 | N6 | Token de paginação sem assinatura | Média | `pagination_token.py` | `LastEvaluatedKey` em base64 pode ser montado pelo cliente (contra a ADR-0014) | Junto do DT-07 |
| DT-23 | N7 | Contrato com o Apex é o formato do banco | Média | `sync_forms_origin_usecase.py` | Mudar o Dynamo muda o que o Apex recebe | Junto do DT-06 |
| DT-24 | N8 | Chamada ao Apex sem credencial | Média | `origin_repository_apex.py` | Só `Content-Type`; hipótese de endpoint público | Ver "Dependências externas" |
| DT-25 | N9 | CORS aberto e `/docs` público | Média | `iac/iac/iac_stack.py:60-62` | Qualquer origem; documentação sem autenticação | Junto do DT-26 |
| DT-26 | N10 | IAM amplo no Cognito | Média | `iac/iac/iac_stack.py:126` | `cognito-idp:*` para as Lambdas | Junto do DT-25 |
| DT-27 | N11 | CD com chave AWS fixa | Média | `.github/workflows/CD.yml` | Chave de longa duração em vez de OIDC; sem o context das origens | Junto do DT-08 |
| DT-28 | N12 | Lambdas em Python 3.10 | Média | `iac/iac/lambda_stack.py:25,49,449` | Fora do suporte da comunidade em outubro de 2026 | Próprio |
| DT-29 | N13 | `ws_server` não escala | Média | `ws_server/presence.py`, `auth.py` | boto3 bloqueante em código async; conexões em memória | Junto do DT-10 |
| DT-30 | N14 | `GSI1SK` com status desatualizado | Média | `form_repository_dynamo.py` (`update_form`) | O `update_form` não reescreve o `GSI1SK` (conferido em 19/11); impacto a medir | Próprio |
| DT-31 | N15 | Cache do service worker por endereço | Média | informs-front `vite.config.ts` | Hipótese de dado de uma pessoa aparecer para outra | Investigar; a versão de 16/11 tirou o cache de API do service worker |
| DT-32 | N16 | OpenAPI põe parâmetro de GET no corpo | Baixa | `src/modules/docs/` | O front sobrescreve à mão em `api.paths.ts` | Próprio |
| DT-33 | N17 | Respostas 204 com corpo | Baixa | `http_codes.py` | O Playwright rejeita; proxies podem descartar | Próprio |
| DT-34 | N18 | Arquivos indevidos no git | Baixa | `git ls-files` nos dois repositórios | `.idea/`, `.claude/`, `native.zip`, `.tanstack/tmp` e outros | Limpeza num PR |
| DT-35 | N19 | ADRs implementadas ainda "Proposto" | Baixa | `docs/adr/` | ADRs 0020, 0024, 0025 e 0026 | Limpeza |
| DT-36 | N20 | Documentação desatualizada | Baixa | este arquivo, ADR-0014, `base.py:12` | DT-05 dizia carga completa de hora em hora (o app faz a cada 6 h); a ADR-0014 cita `last_form_id`; comentário errado em `base.py` | **Parcial (19/11):** corrigido neste arquivo; ADR-0014 e `base.py` continuam abertos |

---

## Dependências externas e decisões pendentes

Não são débito do código; dependem de resposta de outro time ou de decisão. Levantadas em 11/11 e revistas em 19/11.

| Pendência | Quem resolve | Observação |
| --- | --- | --- |
| Autenticação do `POST /forms` (entrada do Apex) e do callback | Apex / Informs | Não achei evidência no código lido; confirmar antes de desenhar a fronteira de segurança. |
| Endpoint e ligação do sync em HML | Rodrigo | O sync entrou em DEV em 04/11 e roda a cada 5 minutos desde 16/11 (#116, `rate(5 minutes)` em `iac/iac/lambda_stack.py:493`); HML não está confirmado, e `homolog` está parada em 31/08 (DT-08). |
| Uberlândia em PROD | Rodrigo / Curci | Só está habilitada em DEV (`apex_sync_enabled_origins=uberlandia`). |
| `RECONCILE_SYSTEMS` sem `UBERLANDIA` | Rodrigo | A reconciliação registra aviso e não monitora a origem (pendência da ADR-0021). |
| Região AWS da arquitetura | Rodrigo | Os recursos de DEV, HML e PROD estão em `sa-east-1`, na mesma conta (conferido em 19/11). Falta registrar isso numa ADR; o código não fixa a região. |
| Nota do vault `📄 Informs` sobre o intervalo do sync | Rodrigo | Esta linha dizia que a nota (5 min) estava desatualizada. Desde 16/11 (#116) o código também usa 5 minutos, então a nota está certa. Fica no vault, não aqui. |
