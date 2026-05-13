# ADR 0017 — Roles do tracking reusam o enum Profile (INSPECTOR/ADMIN)

**Status:** Aceito
**Data:** 2026-05-13
**Contexto:** PRs #45/#46/#47 (feature de tracking realtime via WebSocket).

## Contexto

A tabela `informs-tracking-profile-{stage}` (ADR #16) tem hoje dois papéis
aplicacionais: `ADMIN` e `INSPECTOR`. O serviço de tracking precisa
diferenciar quem **emite** localizações (no campo) de quem **consome** o
stream em tempo real (na operação).

Decisão necessária: introduzir papéis novos no enum (ex: `MOTOCA`/`GESTOR`)
ou reusar os papéis existentes diretamente.

## Decisão

**Reusar `INSPECTOR` e `ADMIN` diretamente, sem tradução.**

- `INSPECTOR` — emite localizações no WS (1 sessão por user, segunda kicka
  a primeira pra evitar pings duplicados).
- `ADMIN` — consome o stream em tempo real (broadcast global, read-only).

Outras roles são rejeitadas no handshake (`AuthError` → close code 4401).

## Razões

1. **Zero migração de dados.** Usuários já cadastrados como INSPECTOR ou
   ADMIN passam a poder usar o tracking sem touch de DDB.
2. **Modelagem operacional bate.** Quem inspeciona forms em campo
   (INSPECTOR) é a mesma persona que vai emitir localização. Quem
   administra a operação (ADMIN) é quem vai monitorar.
3. **Sem indireção.** Iteração anterior do código tinha um `_PROFILE_TO_TRACKING`
   traduzindo INSPECTOR→MOTOCA / ADMIN→GESTOR; isso adicionava nomes
   próprios ao tracking sem ganho semântico — o operador de suporte
   precisava lembrar 2 conjuntos de termos. Removido.
4. **Não compromete o RBAC do REST.** A lambda do REST continua usando
   `ProfileRole.ADMIN`/`INSPECTOR` puros, sem qualquer interferência.

## Consequências

**Positivas**
- Vocabulário único entre REST e tracking. Suporte e logs ficam consistentes.
- Adicionar uma role nova (ex: `OBSERVER`) é atualizar o enum + a lista
  `_ALLOWED_ROLES` em `ws_server/auth.py`.

**Negativas**
- Os papéis `INSPECTOR`/`ADMIN` agora têm responsabilidades em 2 contextos
  (REST + tracking). Se um dia a semântica precisar divergir (ex: ADMIN
  do REST não deveria poder monitorar tracking), aí sim vale segregar.

## Alternativas consideradas

- **Adicionar MOTOCA/GESTOR ao enum ProfileRole** (avaliado e descartado):
  exigiria migração de todos os profiles existentes (script + janela) e
  cria 4 papéis num módulo só (RBAC do REST), sendo que metade não tem uso
  no REST.
- **Tabela Profile separada só pro tracking**: isolamento total, mas
  duplica o cadastro de usuários e cria nova fonte de divergência.
- **Mapping interno (INSPECTOR→MOTOCA, ADMIN→GESTOR)**: foi a 1ª iteração
  do código no PR #46, removida por adicionar termos sem ganho.

## Referências

- ADR #16 — RBAC com Profile em tabela separada
- PR #45 — TrackingStack (CDK)
- PR #46 — WS server (FastAPI + websockets)
- PR #47 — Deploy + ADR (este documento)
