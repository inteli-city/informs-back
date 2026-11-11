# Débito técnico

Itens conhecidos, com o motivo de existirem e o que resolveria cada um. Levantados em 2026-11-11 na revisão da arquitetura Informs × Apex, lendo o código de `origin/dev` (`ab19eea`, merge do #108) contra as ADRs. Nada aqui foi provado em ambiente rodando: cada item cita o arquivo e a linha em que a evidência está.

Ordenados por risco.

**Estado de cada item:** a linha **Estado**, logo abaixo do título, diz se está aberto, parcial ou resolvido. Item resolvido continua no arquivo: o parágrafo **Resolvido (data)** registra como foi resolvido. Só se marca resolvido o que foi conferido no código ou no ambiente.

**O que é débito técnico aqui:** algo no código ou no modelo de dados que se sabe diferente do que a ADR diz ou comprometido, com o motivo e a solução. Não é débito, e fica em outro lugar:

| O quê | Onde |
| --- | --- |
| Decisão de negócio ou resposta de outro time ainda pendente | seção "Dependências externas e decisões pendentes", no fim deste arquivo |
| Passo de implantação (deploy, variável do CDK) | `README.md` e a ADR que o define |

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

## Dependências externas e decisões pendentes

Não são débito do código; dependem de resposta de outro time ou de decisão. Levantadas na mesma revisão.

| Pendência | Quem resolve | Observação |
| --- | --- | --- |
| Autenticação do `POST /forms` (entrada do Apex) e do callback | Apex / Informs | Não achei evidência no código lido; confirmar antes de desenhar a fronteira de segurança. |
| Endpoint e ligação do sync em HML | Rodrigo | O sync de hora em hora entrou em DEV em 04/11; HML não está confirmado. |
| Uberlândia em PROD | Rodrigo / Curci | Só está habilitada em DEV (`apex_sync_enabled_origins=uberlandia`). |
| `RECONCILE_SYSTEMS` sem `UBERLANDIA` | Rodrigo | A reconciliação registra aviso e não monitora a origem (pendência da ADR-0021). |
| Região AWS da arquitetura | Rodrigo | Não achei a região no código lido; o desenho não tem fronteira de região. |
| Nota do vault `📄 Informs` diz sync de 5 min | Rodrigo | O código usa `rate(1 hour)` (#108); a nota está desatualizada. Fica no vault, não aqui. |
