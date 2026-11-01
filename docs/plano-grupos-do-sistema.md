# Plano — Grupos do sistema (IN-1.1)

**Status**: em execução na branch `feature/grupos-do-sistema` (back e front)
**Data**: 2026-11-01
**Decisão de arquitetura**: [ADR-0022](adr/0022-grupos-do-sistema.md)
**Par no front**: `informs-front/docs/plans/grupos-do-sistema.md`

## De onde vem

O planejamento 2027 do Informs (`ilum-planejamento/planejamento-2027/software/informs-objetivos-em-discussao.md`,
v0.2 de 31/10/2026) define quatro funcionalidades para Uberlândia entrar 100% no Informs (bloco IN-1):
grupos, ícones por tipo, camada de satélite e rastreio/rota testados. **Os grupos são a única bloqueante.**

O item IN-1.1 diz:

> Um formulário aberto pode ser direcionado a grupos do sistema: com `grupos` e sem `usuario_id`, só quem
> está num dos grupos pode pegá-lo; com `usuario_id`, só aquela pessoa; sem nenhum dos dois, qualquer
> pessoa do sistema.

Evidência de conclusão pedida pelo planejamento:

> Cenário de Uberlândia com os grupos A (usuários 1 a 5) e B (6 a 10): um formulário com `grupos: [A]`
> aparece só para 1 a 5; com `usuario_id: 2`, só para o 2; sem nenhum dos dois, para os 10.

A especificação de Uberlândia ([especificacao-uberlandia-sgisv.md](especificacao-uberlandia-sgisv.md))
já tinha construído o formulário aberto (pool, `possession`, `claim`/`release`/`assign`, GSI3 esparso) e
deixou o "filtro fino por escopo" para a Fase 2, com `Form.attributes`/`Profile.scope` genéricos. Os grupos
são essa Fase 2 no formato que o planejamento fechou: uma lista explícita de grupos, cadastrados no
Informs, em vez de interseção de atributos livres.

## A regra

| Formulário | Quem vê no pool e pode pegar |
| --- | --- |
| com `user_id` | só aquela pessoa (direcionado, igual a hoje) |
| sem `user_id`, com `groups` | quem tem ao menos um desses grupos no sistema |
| sem nenhum dos dois | qualquer pessoa do sistema (igual a hoje; GAIA e GIPAV ficam aqui) |

- Quem tem `forms.view_all` continua vendo tudo pela visão "Todas" e consegue abrir a ficha de uma OS
  aberta fora dos seus grupos. **Pegar** do pool exige estar no grupo; o gestor direciona pelo `assign`.
- Um formulário direcionado pode ter `groups`: eles passam a valer se ele for devolvido ao pool.

## Decisões tomadas (01/11/2026, com o responsável)

| # | Decisão | Por quê |
| --- | --- | --- |
| G1 | Os grupos são cadastrados e mantidos **no Informs** (admin), por sistema. O Apex pode usar os mesmos endpoints | O contrato é o do Informs (decisão P2 da especificação) |
| G2 | O grupo tem um **identificador curto, escolhido na criação e imutável** (`equipe-leste`) e um nome de exibição editável | É o identificador que o sistema de origem manda no `POST /forms` |
| G3 | `POST /forms` com grupo inexistente responde **400** | Um erro de digitação deixaria a OS invisível para todos |
| G4 | O `assign` do gestor **não** exige que a pessoa esteja no grupo | É um direcionamento explícito, como o `user_id` |
| G5 | Apagar um grupo é **bloqueado** enquanto houver pessoa nele ou OS aberta apontando para ele | Mesmo critério dos papéis ("apaga um role sem ninguém") |
| G6 | O grupo mora no **vínculo da pessoa com o sistema** (`SystemMembership.groups`); quem não tem vínculo não tem grupo | O vínculo já é o lugar do "o que a pessoa é neste sistema" (ADR-0020) |
| G7 | Gerir grupos é a ação nova `groups.manage`; colocar pessoas em grupos usa `users.manage` | Separar o catálogo de grupos de quem distribui as pessoas |

## O que muda no back

### Domínio e gravação
- `Form.groups: List[str]` (vazio = sem restrição). Gravado no item só quando não vazio.
- `SystemMembership.groups: List[str]`. `put_system_user` e o login preservam os grupos ao gravar o vínculo.
- Entidade nova `SystemGroup` (`system`, `group_id`, `name`) na tabela de Profiles,
  `PK = system#{system}` / `SK = group#{group_id}`, ao lado dos roles.
- `create_form` aceita `groups` e valida que cada um existe no sistema (G3).

### Onde o filtro entra
Os três caminhos até uma OS aberta:

| Caminho | Regra |
| --- | --- |
| `GET /forms?scope=pool` | `FilterExpression` no GSI3: `attribute_not_exists(groups)` ou `contains(groups, g)` para cada grupo de quem pede |
| `GET /forms/{id}` | OS aberta com grupos: só quem está num deles ou tem `forms.view_all` |
| `POST /forms/{id}/claim` | OS aberta com grupos: só quem está num deles (403) |

Os grupos de quem pede saem de `AccessControl.groups_in(user_id, system)`, uma leitura do vínculo.

### Endpoints novos
| Rota | Permissão |
| --- | --- |
| `GET /systems/{system}/groups` | `groups.manage` ou `users.manage` |
| `POST /systems/{system}/groups` | `groups.manage` |
| `PUT /systems/{system}/groups/{group_id}` (só o nome) | `groups.manage` |
| `DELETE /systems/{system}/groups/{group_id}` | `groups.manage` (G5) |
| `PUT /systems/{system}/users/{user_id}/groups` | `users.manage` |

`GET /systems/{system}/users` passa a devolver os grupos de cada pessoa, e o `FormResponseSchema` devolve
`groups`.

### Ponto de atenção
O `Limit` do DynamoDB conta os itens **antes** do filtro. Com o filtro de grupos, uma página do pool pode
voltar com menos itens que o limite e um token para continuar; o front já percorre todas as páginas. Medir
o tempo no DEV com o volume real de Uberlândia (o `POOL_DEFAULT_LIMIT` existe por causa do timeout de 15 s).

## O que muda no front
Ver `informs-front/docs/plans/grupos-do-sistema.md`.

## Contrato para o Apex de Uberlândia
- `POST /forms` aceita `groups: string[]` (identificadores do G2). Sem `user_id` e com `groups`, a OS fica
  no pool só para esses grupos.
- Os identificadores vêm de `GET /systems/UBERLANDIA/groups` (ou são combinados na criação dos grupos).

## Fora do escopo
- Grupos vindos do Cognito ou do Apex automaticamente.
- Filtro por grupo em `scope=mine` e `scope=all` (não se aplica: são OS com dono ou a visão do gestor).
- Ícones, satélite e rastreio (IN-1.2 a IN-1.4).

## Como validar (evidência do IN-1.1)
1. Testes dos usecases com o cenário A (usuários 1 a 5) e B (6 a 10): `tests/modules/get_all_forms`,
   `get_form`, `claim_form`.
2. No DEV: criar A e B em `UBERLANDIA`, distribuir 10 contas de teste e criar três OS
   (`groups: [A]`, `user_id` do usuário 2, sem nenhum dos dois); conferir quem vê cada uma no PWA.
