# ADR-0008: Ciclo de Vida do Formulário (State Machine)

**Status**: Aceito

**Data**: 2025-01-01

**Decisores**: Equipe Intelicity

**Tags**: domínio, formulário, state-machine, ciclo-de-vida, status

## Contexto

Formulários passam por diferentes estados ao longo de sua vida — da criação ao preenchimento ou cancelamento. Precisávamos de regras claras sobre:

- Quais transições de estado são válidas
- Quem pode executar cada transição
- Quais dados são registrados em cada transição (timestamps)
- Como impedir operações inválidas (ex: submeter um formulário já cancelado)

## Decisão

Implementamos um **ciclo de vida com 5 estados** e transições controladas nos usecases.

**Estados (FORM_STATUS):**
```
PENDING → IN_PROGRESS → COMPLETED → SENT
                      ↘ CANCELLED
PENDING → CANCELLED
```

| Status | Descrição |
|--------|-----------|
| `PENDING` | Formulário criado, aguardando início |
| `IN_PROGRESS` | Usuário iniciou o preenchimento |
| `COMPLETED` | Formulário submetido com todos os campos preenchidos |
| `SENT` | Formulário sincronizado com sucesso ao sistema de origem |
| `CANCELLED` | Formulário cancelado com justificativa |

**Transições e módulos responsáveis:**

| De | Para | Módulo | Validações |
|----|------|--------|------------|
| `PENDING` | `IN_PROGRESS` | `start_form` | Usuário é o destinatário |
| `IN_PROGRESS` | `COMPLETED` | `submit_form` | Campos obrigatórios preenchidos |
| `PENDING/IN_PROGRESS` | `CANCELLED` | `cancel_form` | Justificativa válida (opção, texto/imagem se obrigatórios) |
| `COMPLETED` | `SENT` | `sync_forms_origin` | Envio ao sistema de origem com sucesso |

**Timestamps registrados:**
- `created_at` — na criação (create_form)
- `in_progress_at` — ao iniciar (start_form)
- `completed_at` — ao submeter (submit_form, enviado pelo cliente)
- `cancelled_at` — ao cancelar (cancel_form, enviado pelo cliente)
- `updated_at` — em qualquer alteração

**Proteções nos usecases:**
```python
# start_form
if form.status is not FORM_STATUS.PENDING:
    raise ForbiddenAction("Formulário não está pendente")

# submit_form
if form.status is not FORM_STATUS.IN_PROGRESS:
    raise ForbiddenAction("Formulário não está em andamento")

# cancel_form
if form.status in [FORM_STATUS.CANCELLED, FORM_STATUS.COMPLETED]:
    raise ForbiddenAction("Formulário já está finalizado")
```

**Autorização:**
- Todas as transições verificam: `user_id == form.user_id`
- O `created_by` (quem criou) pode ser diferente do `user_id` (destinatário)

## Consequências

### Positivas
- Transições de estado são explícitas e validadas em cada usecase
- Timestamps por transição permitem auditoria completa do ciclo de vida
- Impossível atingir estados inválidos (ex: COMPLETED sem passar por IN_PROGRESS)
- Separação entre criador (`created_by`) e executor (`user_id`) permite delegação

### Negativas
- Status `SENT` é controlado pelo sync e não tem endpoint direto — visibilidade limitada
- Cancelamento permite pular `IN_PROGRESS` (direto de PENDING), podendo ser confuso
- Sem histórico de transições — apenas o status atual e timestamps são persistidos

## Alternativas Consideradas

### Estado implícito (sem enum)
- **Descrição**: Derivar estado dos timestamps existentes (ex: se completed_at != null → COMPLETED)
- **Motivo da rejeição**: Queries complexas para filtrar por status; lógica de derivação espalhada; propenso a ambiguidades

### State Machine formal (transitions/pytransitions)
- **Descrição**: Usar biblioteca de state machine com definição declarativa de estados e transições
- **Motivo da rejeição**: Overhead de dependência para um ciclo de vida relativamente simples; validações nos usecases são claras e suficientes
