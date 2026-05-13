# ADR 0017 — Mapeamento de roles do tracking sobre o Profile existente

**Status:** Aceito
**Data:** 2026-05-13
**Contexto:** PRs #45/#46/#47 (feature de tracking realtime via WebSocket).

## Contexto

A tabela `informs-tracking-profile-{stage}` (ADR #16) tem hoje só dois
papéis aplicacionais: `ADMIN` e `INSPECTOR`. O serviço de tracking introduz
dois papéis novos no domínio do produto: **MOTOCA** (motoverificador que
emite localizações) e **GESTOR** (operador que consome o stream realtime).

Decisão necessária: criar valores novos no enum `ProfileRole` (e migrar
usuários existentes) ou reusar os papéis atuais com semântica nova.

## Decisão

**Reusar os papéis existentes com mapeamento aplicado dentro do tracking:**

- `INSPECTOR` → MOTOCA
- `ADMIN`     → GESTOR

O enum `ProfileRole` permanece intacto. O mapeamento vive em
`ws_server/auth.py` (`_PROFILE_TO_TRACKING`) e é o único lugar do código
que conhece a equivalência.

## Razões

1. **Zero migração de dados.** Usuários hoje cadastrados como INSPECTOR no
   homolog/prod já passam a poder usar tracking sem touch de DDB.
2. **Modelagem operacional bate.** Quem inspeciona forms em campo
   (INSPECTOR) é a mesma persona que vai abrir o app de moto. Quem
   administra a operação (ADMIN) é quem vai monitorar a frota.
3. **Acoplamento contido.** O conhecimento do mapping fica numa única
   função privada; a expansão futura (separar os enums) é trivial — basta
   adicionar valores novos e estender o dicionário.
4. **Não compromete o RBAC do REST.** A lambda do REST continua usando
   `ProfileRole.ADMIN`/`INSPECTOR` puros, sem saber de MOTOCA/GESTOR.

## Consequências

**Positivas**
- Deploy do tracking não exige passo de migração.
- Pessoas com role INSPECTOR ou ADMIN no Profile já têm acesso definido.

**Negativas**
- Termo "MOTOCA" só aparece no contexto do tracking (no banco continua
  `INSPECTOR`). Operadores de suporte precisam saber dessa equivalência.
- Se um dia precisarmos de uma role tipo `OBSERVER` (gestor read-only que
  não pode admin de forms), vai exigir migração — mas nesse momento já
  vale a pena introduzir um enum próprio do tracking.

## Alternativas consideradas

- **Adicionar MOTOCA/GESTOR ao enum ProfileRole**: coerente com o domínio
  mas exige migração de todos os profiles existentes (script + janela) e
  cria 4 papéis num módulo só (RBAC do REST), sendo que metade não tem uso
  no REST. Avaliado como over-engineering pra fase atual.
- **Tabela Profile separada só pro tracking**: isolamento total, mas
  duplica o cadastro de usuários e cria nova fonte de divergência.

## Referências

- ADR #16 — RBAC com Profile em tabela separada
- PR #45 — TrackingStack (CDK)
- PR #46 — WS server (FastAPI + websockets)
- PR #47 — Deploy + ADR (este documento)
